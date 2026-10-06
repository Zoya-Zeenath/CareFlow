# CareFlow — Clinical Pathway Process Mining

**Domain:** Healthcare Operations & Process Analytics

## Problem Statement

Hospital administrators don't know why Emergency Room wait times are so high. Standard BI dashboards show the "average wait time," but they can't map the chaotic, real-world sequence of events a patient actually experiences — obscuring the true operational bottlenecks.

## Use Case

A hospital administrator uses CareFlow. The pipeline ingests raw, timestamped event logs from the hospital's Electronic Health Record (EHR) system (e.g., *Patient A: Triage at 10:00 → X-Ray at 10:15 → Triage at 10:30*). Using process mining algorithms, it generates a visual "Spaghetti Diagram" of actual patient flows.

The dashboard highlights a hidden bottleneck: **40% of patients are sent back to Triage after an X-Ray** due to a specific missing paperwork form. The administrator updates the intake form, instantly reducing average wait times by 20 minutes.

## Key Modules

| Module | Tool | Purpose |
|---|---|---|
| Data Warehouse | Google BigQuery | Highly performant storage for massive volumes of chronological healthcare event logs |
| Process Mining Engine | PM4Py (Python) | Discovers process models (Petri nets, Directed Graphs) directly from raw timestamped event data |
| Data Transformation | dbt | Pre-processes messy EHR logs into strict standard formatting (Case_ID, Activity_Name, Timestamp) |
| Process Dashboard | Microsoft PowerBI / Looker | BI report with custom process-flowchart visuals alongside standard operational KPIs |

## Week-wise Development Plan

| Week | Event Log Engineering (BigQuery, dbt) | Process Mining & BI (PM4Py, PowerBI) |
|---|---|---|
| **Week 1** | **EHR Simulation:** Build a Python script generating mock hospital event logs, deliberately coding in operational inefficiencies and loop-backs. | **Warehouse Setup:** Load the raw event logs into BigQuery. Configure dbt for the initial cleaning phase. |
| **Week 2** | **Event Normalization:** Write dbt models to standardize the data into an "Event Log" format required by process mining algorithms. | **Process Discovery:** Use the PM4Py library to ingest the dbt output and algorithmically discover the "As-Is" process map of the hospital. |
| **Mid-Project Review** | Ensure the simulated data flows seamlessly from the Python generator into clean, chronological BigQuery tables. | Prove PM4Py successfully generates a Directed Graph showing the major paths patients take through the hospital. |
| **Week 3** | **Bottleneck Calculations:** Write SQL/Python logic to calculate the average transition time between every single event (e.g., Average time from Triage to Doctor). | **BI Dashboard:** Connect PowerBI to BigQuery. Import custom process mining visuals (like the Power Automate Process Mining visual). |
| **Week 4** | **Conformance Checking:** Implement logic to compare the *actual* patient journey against the hospital's *ideal/mandated* journey, flagging non-compliant paths. | **Refine & Polish:** Polish the dashboard, adding drill-down capabilities so administrators can filter the process map by specific patient demographics or doctors. |
| **Final Review** | A niche, highly valuable data engineering skill utilizing event-log architecture rather than standard relational tables. | An enterprise healthcare operations dashboard revealing hidden organizational friction. |

## Tech Stack

- **Storage:** Google BigQuery
- **Transformation:** dbt (Data Build Tool)
- **Process Mining:** PM4Py (Python)
- **Visualization:** Microsoft PowerBI / Looker
- **Language:** Python, SQL

## Project Status

🚧 In development — see the week-wise plan above for current progress.
