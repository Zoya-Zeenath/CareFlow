-- CareFlow mid-project "Pipeline Audit": is the data clean, complete and chronological?
-- Run each block in the BigQuery console.

-- 1) Row counts at each layer (raw -> staging -> event log)
SELECT 'raw'      AS layer, COUNT(*) AS n FROM `careflow-511009.careflow_raw.ehr_events_raw`
UNION ALL
SELECT 'staging'  AS layer, COUNT(*) FROM `careflow-511009.careflow_dbt.stg_ehr_events`
UNION ALL
SELECT 'event_log (complete only)', COUNT(*) FROM `careflow-511009.careflow_dbt.event_log`;

-- 2) Patients and date range
SELECT COUNT(DISTINCT case_id) AS patients, MIN(timestamp) AS first_event, MAX(timestamp) AS last_event
FROM `careflow-511009.careflow_dbt.event_log`;

-- 3) Chronology check: events out of order within a patient (expect 0)
SELECT COUNT(*) AS out_of_order_events
FROM (
  SELECT timestamp,
         LAG(timestamp) OVER (PARTITION BY case_id ORDER BY event_seq) AS prev_ts
  FROM `careflow-511009.careflow_dbt.event_log`
)
WHERE timestamp < prev_ts;

-- 4) Activity frequency
SELECT activity_name, COUNT(*) AS events
FROM `careflow-511009.careflow_dbt.event_log`
GROUP BY 1 ORDER BY events DESC;

-- 5) Quick preview of one patient's journey
SELECT case_id, event_seq, activity_name, timestamp
FROM `careflow-511009.careflow_dbt.event_log`
WHERE case_id = 'P000002'
ORDER BY event_seq;
