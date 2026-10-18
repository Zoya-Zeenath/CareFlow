"""
CareFlow - What-if simulation
-----------------------------
Answers: "If the administrator fixes the intake form, how much do waits drop?"

Runs the SAME hospital under different scenarios, over several random seeds
(a single run could be luck), and compares the averages.

    baseline        today's ER (40% of X-ray patients sent back to Triage)
    fix_paperwork   intake form fixed -> nobody is sent back
    second_xray     no form fix, but a 2nd X-ray machine
    both            form fixed AND a 2nd X-ray machine

Run from D:\\careflow\\simulator:
    python what_if.py                 # 10 seeds, 30 days each (~1-2 min)
    python what_if.py --seeds 5       # quicker
Output: ../data/what_if_results.csv  and  ../data/what_if_summary.csv
"""
import argparse

import pandas as pd

import simulate_er as sim

SCENARIOS = {
    "baseline":      dict(loopback_prob=None, xray_capacity=1),
    "fix_paperwork": dict(loopback_prob=0.0,  xray_capacity=1),
    "second_xray":   dict(loopback_prob=None, xray_capacity=2),
    "both":          dict(loopback_prob=0.0,  xray_capacity=2),
}


def metrics(df: pd.DataFrame) -> dict:
    """Headline numbers for one simulation run."""
    stay = df.groupby("case_id").timestamp.agg(lambda s: (s.max() - s.min()).total_seconds() / 60)

    # queue wait before each activity = this START minus the previous event's time
    d = df.sort_values(["case_id", "timestamp"]).copy()
    d["prev_ts"] = d.groupby("case_id").timestamp.shift()
    starts = d[d.lifecycle == "start"].copy()
    starts["wait"] = (starts.timestamp - starts.prev_ts).dt.total_seconds() / 60

    xray_wait = starts.loc[starts.activity == "X-Ray", "wait"]
    return {
        "patients": stay.size,
        "avg_stay_min": stay.mean(),
        "p90_stay_min": stay.quantile(0.9),
        "avg_xray_wait_min": xray_wait.mean(),
        "avg_total_wait_min": starts.groupby("case_id").wait.sum().mean(),
        "sent_back": df[df.activity == "Re-Triage"].case_id.nunique(),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--days", type=int, default=30)
    args = ap.parse_args()

    rows = []
    for name, cfg in SCENARIOS.items():
        for seed in range(1, args.seeds + 1):
            df = sim.run(days=args.days, seed=seed, **cfg)
            rows.append({"scenario": name, "seed": seed, **metrics(df)})
            print(f"  {name:14s} seed {seed:2d} done")
    res = pd.DataFrame(rows)
    res.to_csv("../data/what_if_results.csv", index=False)

    # average over seeds + paired difference vs baseline (same seed = same demand)
    cols = ["avg_stay_min", "p90_stay_min", "avg_xray_wait_min", "avg_total_wait_min", "sent_back"]
    avg = res.groupby("scenario")[cols].mean().round(1)
    base = res[res.scenario == "baseline"].set_index("seed")[cols]
    diffs = {}
    for name in SCENARIOS:
        cur = res[res.scenario == name].set_index("seed")[cols]
        d = (cur - base)
        diffs[name] = d["avg_stay_min"].mean(), d["avg_stay_min"].std(), d["avg_total_wait_min"].mean()
    avg["stay_change_vs_baseline"] = [round(diffs[n][0], 1) for n in avg.index]
    avg["stay_change_std_across_seeds"] = [round(diffs[n][1], 1) for n in avg.index]
    avg["total_wait_change_vs_baseline"] = [round(diffs[n][2], 1) for n in avg.index]
    avg = avg.loc[list(SCENARIOS)]
    avg.to_csv("../data/what_if_summary.csv")

    print(f"\nAverages over {args.seeds} seeds ({args.days} days each):\n")
    print(avg.to_string())


if __name__ == "__main__":
    main()
