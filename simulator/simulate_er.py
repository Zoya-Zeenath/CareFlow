"""
CareFlow - Step 1: Emergency Room event-log simulator
-----------------------------------------------------
Simulates patients moving through a hospital ER and writes every step
as an event row (the raw "EHR log" our pipeline will ingest).

Why SimPy and not random timestamps?
  Resources are LIMITED (few doctors, 1 X-ray machine). When patients
  arrive faster than staff can serve them, queues form on their own.
  So bottlenecks EMERGE from the system instead of being hard-coded.

Run:  python simulate_er.py --days 30 --seed 42
Out:  ../data/ehr_events_raw.csv
"""
import argparse
import random
from datetime import datetime, timedelta

import pandas as pd
import simpy

# ----------------------------------------------------------------------
# 1. CONFIG - change these numbers to change hospital behaviour
# ----------------------------------------------------------------------
START_DATE = datetime(2026, 1, 1, 0, 0, 0)

CAPACITY = {          # how many of each resource the ER has
    "registration": 2,
    "triage": 3,
    "doctor": 4,
    "xray": 1,        # <-- deliberately scarce: classic bottleneck
    "lab": 2,
    "treatment": 6,   # treatment bays (separate from doctors)
}

# Average service time in MINUTES (we draw from an exponential-ish spread)
SERVICE_MIN = {
    "Registration": 4,
    "Triage": 8,
    "Doctor Consultation": 15,
    "X-Ray": 12,
    "Lab Test": 20,
    "Treatment": 25,
    "Re-Triage": 6,
}

# Patients arriving per hour, by hour of day (evening rush, quiet at night)
ARRIVALS_PER_HOUR = [
    2, 2, 1, 1, 1, 2, 3, 5, 7, 8, 8, 9,
    9, 8, 8, 9, 10, 12, 14, 14, 11, 8, 5, 3,
]

# Severity (ESI): 1 = critical ... 5 = minor. Mostly 3s in real ERs.
SEVERITY_WEIGHTS = {1: 0.03, 2: 0.15, 3: 0.42, 4: 0.28, 5: 0.12}

# THE HIDDEN INEFFICIENCY (matches the project doc):
# After X-Ray, some patients are sent BACK to triage because the
# intake paperwork form was incomplete.
PAPERWORK_LOOPBACK_PROB = 0.40
# ...and it only happens to patients who had an X-ray, mostly when the
# form was missed at registration:
MISSING_FORM_PROB = 0.40


# ----------------------------------------------------------------------
# 2. HELPERS
# ----------------------------------------------------------------------
def to_clock(sim_minutes: float) -> datetime:
    """Convert simulation minutes into a real timestamp."""
    return START_DATE + timedelta(minutes=sim_minutes)


def service_time(activity: str) -> float:
    """Random duration around the average (never less than 1 minute)."""
    mean = SERVICE_MIN[activity]
    return max(1.0, random.gammavariate(2.0, mean / 2.0))


class ER:
    """The hospital: holds resources and the event log."""

    def __init__(self, env: simpy.Environment):
        self.env = env
        # PriorityResource -> sicker patients (low severity number) jump the queue
        self.res = {name: simpy.PriorityResource(env, cap) for name, cap in CAPACITY.items()}
        self.events = []

    def log(self, case_id, activity, lifecycle, resource_name, severity, age_group, gender):
        self.events.append({
            "case_id": case_id,
            "activity": activity,
            "lifecycle": lifecycle,            # 'start' or 'complete'
            "timestamp": to_clock(self.env.now),
            "resource": resource_name,
            "severity": severity,
            "age_group": age_group,
            "gender": gender,
        })

    def do_step(self, patient, activity, res_key):
        """
        One step of care: wait in queue -> get a staff member -> be served.
        Logs 'start' when service begins (so queue wait = previous complete -> this start)
        and 'complete' when it ends.
        """
        case_id, severity, age_group, gender = patient
        with self.res[res_key].request(priority=severity) as req:
            yield req                                            # waiting in queue
            staff_id = f"{res_key}_{random.randint(1, CAPACITY[res_key])}"
            self.log(case_id, activity, "start", staff_id, severity, age_group, gender)
            yield self.env.timeout(service_time(activity))       # being served
            self.log(case_id, activity, "complete", staff_id, severity, age_group, gender)


# ----------------------------------------------------------------------
# 3. ONE PATIENT'S JOURNEY
# ----------------------------------------------------------------------
def patient_journey(env, er: ER, case_id: str):
    severity = random.choices(list(SEVERITY_WEIGHTS), weights=SEVERITY_WEIGHTS.values())[0]
    age_group = random.choices(["child", "adult", "senior"], weights=[0.18, 0.55, 0.27])[0]
    gender = random.choice(["F", "M"])
    patient = (case_id, severity, age_group, gender)

    # Arrival
    er.log(case_id, "Arrival", "complete", "front_door", severity, age_group, gender)

    # Registration -> Triage -> Doctor (everyone)
    yield from er.do_step(patient, "Registration", "registration")
    form_missing = random.random() < MISSING_FORM_PROB      # silent problem at the desk
    yield from er.do_step(patient, "Triage", "triage")
    yield from er.do_step(patient, "Doctor Consultation", "doctor")

    # Doctor decides on tests. Sicker patients get more tests.
    needs_xray = random.random() < {1: 0.9, 2: 0.7, 3: 0.55, 4: 0.3, 5: 0.1}[severity]
    needs_lab = random.random() < {1: 0.9, 2: 0.7, 3: 0.4, 4: 0.15, 5: 0.05}[severity]

    if needs_xray:
        yield from er.do_step(patient, "X-Ray", "xray")
        # THE LOOP-BACK: missing paperwork -> sent back to triage -> back to doctor
        if form_missing and random.random() < PAPERWORK_LOOPBACK_PROB / MISSING_FORM_PROB:
            yield from er.do_step(patient, "Re-Triage", "triage")
            yield from er.do_step(patient, "Doctor Consultation", "doctor")

    if needs_lab:
        yield from er.do_step(patient, "Lab Test", "lab")

    # Most patients get treatment (not the minor ones)
    if severity <= 4:
        yield from er.do_step(patient, "Treatment", "treatment")

    # Outcome
    outcome = "Admission" if (severity <= 2 and random.random() < 0.6) else "Discharge"
    er.log(case_id, outcome, "complete", "exit", severity, age_group, gender)


# ----------------------------------------------------------------------
# 4. PATIENT ARRIVALS OVER TIME
# ----------------------------------------------------------------------
def arrival_process(env, er: ER, days: int):
    counter = 0
    horizon = days * 24 * 60
    while env.now < horizon:
        hour = int((env.now // 60) % 24)
        rate_per_min = ARRIVALS_PER_HOUR[hour] / 60.0
        yield env.timeout(random.expovariate(rate_per_min))
        counter += 1
        env.process(patient_journey(env, er, f"P{counter:06d}"))


# ----------------------------------------------------------------------
# 5. MAIN
# ----------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default="../data/ehr_events_raw.csv")
    args = ap.parse_args()

    random.seed(args.seed)
    env = simpy.Environment()
    er = ER(env)
    env.process(arrival_process(env, er, args.days))
    env.run()                      # run until all patients are done

    df = pd.DataFrame(er.events).sort_values(["timestamp", "case_id"]).reset_index(drop=True)
    df.to_csv(args.out, index=False)
    print(f"Wrote {len(df):,} events for {df.case_id.nunique():,} patients -> {args.out}")


if __name__ == "__main__":
    main()
