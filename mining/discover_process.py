"""
CareFlow - Week 2: Process discovery with PM4Py
-----------------------------------------------
Reads the event log, discovers the "as-is" process map (Directed Graph),
and prints the headline findings (variants, loop-backs, durations).

Usage (run from D:\\careflow\\mining):
    python discover_process.py --source bigquery     # reads the dbt event_log table
    python discover_process.py --source csv          # fallback: builds the log from the raw CSV

Outputs go to ./output/
"""
import argparse
import os

import pandas as pd
import pm4py

PROJECT_ID = "careflow-511009"
KEY_PATH = r"D:\secrets\gcp-key.json"
EVENT_LOG_TABLE = f"{PROJECT_ID}.careflow_dbt.event_log"
RAW_CSV = r"D:\careflow\data\ehr_events_raw.csv"
OUT_DIR = "output"


# ---------------------------------------------------------------- loading
def load_from_bigquery() -> pd.DataFrame:
    from google.cloud import bigquery

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = KEY_PATH
    client = bigquery.Client(project=PROJECT_ID)
    sql = f"""
        SELECT case_id, activity_name, timestamp
        FROM `{EVENT_LOG_TABLE}`
        ORDER BY case_id, event_seq
    """
    return client.query(sql).to_dataframe()


def load_from_csv() -> pd.DataFrame:
    """Same logic as the dbt event_log model: keep 'complete' events only."""
    raw = pd.read_csv(RAW_CSV, parse_dates=["timestamp"])
    raw = raw[raw["lifecycle"] == "complete"]
    return raw.rename(columns={"activity": "activity_name"})[
        ["case_id", "activity_name", "timestamp"]
    ].sort_values(["case_id", "timestamp"])


# ---------------------------------------------------------------- analysis
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["bigquery", "csv"], default="bigquery")
    args = ap.parse_args()
    os.makedirs(OUT_DIR, exist_ok=True)

    df = load_from_bigquery() if args.source == "bigquery" else load_from_csv()
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    print(f"Loaded {len(df):,} events, {df.case_id.nunique():,} cases (source: {args.source})")

    # PM4Py expects specific column names / types
    log = pm4py.format_dataframe(
        df, case_id="case_id", activity_key="activity_name", timestamp_key="timestamp"
    )

    # 1) Directed graph (Directly-Follows Graph) = the "spaghetti diagram"
    dfg, start_acts, end_acts = pm4py.discover_dfg(log)
    print("\nTop 10 most frequent hand-offs (A -> B : patients):")
    for (a, b), n in sorted(dfg.items(), key=lambda kv: -kv[1])[:10]:
        print(f"  {a:22s} -> {b:22s} {n:6d}")

    dfg_png = os.path.join(OUT_DIR, "process_map_dfg.png")
    try:
        pm4py.save_vis_dfg(dfg, start_acts, end_acts, dfg_png)
        print(f"\nSaved process map -> {dfg_png}")
    except Exception as exc:  # Graphviz missing on this machine
        print(f"\n(Graphviz not available: {exc.__class__.__name__}; using fallback drawing)")
        draw_fallback(dfg, dfg_png)

    # 2) Petri net (formal process model) with the Inductive Miner
    net, im, fm = pm4py.discover_petri_net_inductive(log, noise_threshold=0.2)
    print(f"Petri net: {len(net.places)} places, {len(net.transitions)} transitions")
    try:
        pm4py.save_vis_petri_net(net, im, fm, os.path.join(OUT_DIR, "petri_net.png"))
    except Exception:
        pass

    # 3) Variants = distinct paths patients actually took
    variants = pm4py.get_variants(log)
    ranked = sorted(variants.items(), key=lambda kv: -kv[1])
    print(f"\nDistinct patient paths (variants): {len(ranked)}")
    print("Top 5 variants:")
    for path, n in ranked[:5]:
        print(f"  {n:5d} patients: {' > '.join(path)}")

    # 4) Headline finding: the paperwork loop-back
    xray = set(df[df.activity_name == "X-Ray"].case_id)
    back = set(df[df.activity_name == "Re-Triage"].case_id)
    if xray:
        pct = 100 * len(back & xray) / len(xray)
        print(f"\nLOOP-BACK: {len(back & xray):,} of {len(xray):,} X-ray patients "
              f"({pct:.0f}%) were sent back to Triage")

    # 5) Case duration (arrival -> exit)
    dur = df.groupby("case_id").timestamp.agg(lambda s: (s.max() - s.min()).total_seconds() / 60)
    print(f"Time in ER (min): mean {dur.mean():.0f}, median {dur.median():.0f}, "
          f"p90 {dur.quantile(0.9):.0f}")

    pd.Series(dfg).rename("count").to_csv(os.path.join(OUT_DIR, "dfg_edges.csv"))


def draw_fallback(dfg, path):
    """Simple networkx drawing so the review never depends on Graphviz."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import networkx as nx

    g = nx.DiGraph()
    for (a, b), n in dfg.items():
        if n >= 20:  # hide rare edges so the picture stays readable
            g.add_edge(a, b, weight=n)
    pos = nx.spring_layout(g, seed=7, k=1.6)
    plt.figure(figsize=(13, 8))
    widths = [1 + 6 * d["weight"] / max(dd["weight"] for *_, dd in g.edges(data=True))
              for *_, d in g.edges(data=True)]
    nx.draw_networkx(g, pos, node_color="#cfe3ff", node_size=3200, font_size=8,
                     width=widths, arrowsize=18, connectionstyle="arc3,rad=0.1")
    nx.draw_networkx_edge_labels(g, pos, nx.get_edge_attributes(g, "weight"), font_size=7)
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()


if __name__ == "__main__":
    main()
