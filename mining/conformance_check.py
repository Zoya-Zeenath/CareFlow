"""
CareFlow - Conformance checking
-------------------------------
Compares every patient's ACTUAL journey with the hospital's IDEAL pathway,
flags non-compliant patients, and puts a time cost on each deviation.

Ideal pathway (the "mandated" journey):
    Arrival -> Registration -> Triage -> Doctor Consultation
            -> [X-Ray]? -> [Lab Test]? -> [Treatment]? -> Discharge | Admission
    ([..]? = optional: the doctor only orders it when needed)
    Nothing is allowed to go BACK to Triage, and there is only one consultation
    before tests.

Usage (from D:\\careflow\\mining):
    python conformance_check.py --source bigquery
    python conformance_check.py --source bigquery --upload     # also writes tables for Power BI
    python conformance_check.py --source csv                   # fallback without BigQuery
"""
import argparse
import os

import pandas as pd
import pm4py

PROJECT_ID = "careflow-511009"
KEY_PATH = r"D:\secrets\gcp-key.json"
DATASET = "careflow_dbt"
RAW_CSV = r"D:\careflow\data\ehr_events_raw.csv"
OUT_DIR = "output"

IDEAL_PROCESS = (
    "->('Arrival','Registration','Triage','Doctor Consultation',"
    "X('X-Ray',tau),X('Lab Test',tau),X('Treatment',tau),"
    "X('Discharge','Admission'))"
)


# ---------------------------------------------------------------- loading
def load_from_bigquery() -> pd.DataFrame:
    from google.cloud import bigquery

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = KEY_PATH
    client = bigquery.Client(project=PROJECT_ID)
    sql = f"""
        SELECT case_id, activity_name, timestamp, severity, age_group, gender
        FROM `{PROJECT_ID}.{DATASET}.event_log`
        ORDER BY case_id, event_seq
    """
    return client.query(sql).to_dataframe()


def load_from_csv() -> pd.DataFrame:
    raw = pd.read_csv(RAW_CSV, parse_dates=["timestamp"])
    raw = raw[raw["lifecycle"] == "complete"].rename(columns={"activity": "activity_name"})
    return raw[["case_id", "activity_name", "timestamp", "severity", "age_group", "gender"]]


# ---------------------------------------------------------------- analysis
def describe_deviations(alignment) -> list:
    """Turn one alignment into readable deviations.
    ('Re-Triage', '>>')  = log move   -> patient did something the ideal path forbids
    ('>>', 'X-Ray')      = model move -> an expected step was skipped"""
    out = []
    for log_label, model_label in alignment:
        if model_label == ">>":
            out.append(f"extra: {log_label}")
        elif log_label == ">>" and model_label is not None:
            out.append(f"missing: {model_label}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["bigquery", "csv"], default="bigquery")
    ap.add_argument("--upload", action="store_true", help="write result tables to BigQuery")
    args = ap.parse_args()
    os.makedirs(OUT_DIR, exist_ok=True)

    df = load_from_bigquery() if args.source == "bigquery" else load_from_csv()
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    print(f"Loaded {len(df):,} events, {df.case_id.nunique():,} patients (source: {args.source})")

    # 1) Build the ideal model and align every patient against it
    log_df = pm4py.format_dataframe(
        df[["case_id", "activity_name", "timestamp"]],
        case_id="case_id", activity_key="activity_name", timestamp_key="timestamp",
    )
    event_log = pm4py.convert_to_event_log(log_df)
    case_ids = [t.attributes["concept:name"] for t in event_log]

    tree = pm4py.parse_process_tree(IDEAL_PROCESS)
    net, im, fm = pm4py.convert_to_petri_net(tree)
    alignments = pm4py.conformance_diagnostics_alignments(event_log, net, im, fm)

    rows = []
    for cid, al in zip(case_ids, alignments):
        devs = describe_deviations(al["alignment"])
        rows.append({
            "case_id": cid,
            "fitness": round(al["fitness"], 3),
            "is_compliant": len(devs) == 0,
            "deviations": "; ".join(devs) if devs else "none",
        })
    cases = pd.DataFrame(rows)

    # 2) Time cost of the loop-back: X-Ray complete -> end of the SECOND consultation.
    #    Everything in that window (re-triage queue + re-triage + waiting for the
    #    doctor again + the repeat consultation) exists only because of the loop.
    df = df.sort_values(["case_id", "timestamp"])
    detour = {}
    for cid, g in df.groupby("case_id"):
        acts = g.activity_name.tolist()
        if "Re-Triage" not in acts or "X-Ray" not in acts:
            continue
        xray_done = g.loc[g.activity_name == "X-Ray", "timestamp"].iloc[0]
        doctor_times = g.loc[g.activity_name == "Doctor Consultation", "timestamp"]
        if len(doctor_times) >= 2:
            detour[cid] = (doctor_times.iloc[1] - xray_done).total_seconds() / 60
    cases["detour_minutes"] = cases.case_id.map(detour).round(1)

    stay = df.groupby("case_id").timestamp.agg(lambda s: (s.max() - s.min()).total_seconds() / 60)
    attrs = df.groupby("case_id")[["severity", "age_group", "gender"]].first()
    cases = cases.merge(stay.rename("stay_minutes").round(1), on="case_id") \
                 .merge(attrs, on="case_id")

    # 3) Summaries
    total = len(cases)
    ok = int(cases.is_compliant.sum())
    print(f"\nIdeal pathway followed: {ok:,} of {total:,} patients ({100 * ok / total:.1f}%)")
    print(f"Non-compliant:          {total - ok:,} patients")
    print(f"Average fitness:        {cases.fitness.mean():.3f}  (1.000 = perfect match)")

    dev = cases[~cases.is_compliant]
    summary = (
        dev.groupby("deviations")
        .agg(patients=("case_id", "count"),
             avg_detour_min=("detour_minutes", "mean"),
             avg_stay_min=("stay_minutes", "mean"))
        .round(1).reset_index().sort_values("patients", ascending=False)
    )
    summary["total_detour_hours"] = (summary.patients * summary.avg_detour_min / 60).round(1)
    print("\nDeviation summary:")
    print(summary.to_string(index=False))

    comp_stay = cases[cases.is_compliant].stay_minutes.mean()
    dev_stay = dev.stay_minutes.mean()
    print(f"\nAverage stay: compliant {comp_stay:.0f} min vs non-compliant {dev_stay:.0f} min")
    if len(dev):
        print(f"Loop-back detour: {dev.detour_minutes.mean():.0f} min on average "
              f"({dev.detour_minutes.sum() / 60:,.0f} patient-hours over the period)")

    cases.to_csv(os.path.join(OUT_DIR, "conformance_cases.csv"), index=False)
    summary.to_csv(os.path.join(OUT_DIR, "deviation_summary.csv"), index=False)
    print(f"\nSaved results to {OUT_DIR}/ (conformance_cases.csv, deviation_summary.csv)")

    # 4) Optional: publish to BigQuery so Power BI can read them
    if args.upload:
        from google.cloud import bigquery

        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = KEY_PATH
        client = bigquery.Client(project=PROJECT_ID)
        cfg = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
        for name, frame in [("conformance_cases", cases), ("deviation_summary", summary)]:
            frame = frame.copy()
            table_id = f"{PROJECT_ID}.{DATASET}.{name}"
            client.load_table_from_dataframe(frame, table_id, job_config=cfg).result()
            print(f"Uploaded {len(frame):,} rows -> {table_id}")


if __name__ == "__main__":
    main()
