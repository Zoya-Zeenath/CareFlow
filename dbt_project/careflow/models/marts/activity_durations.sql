-- One row per activity a patient went through (a Doctor Consultation that happens
-- twice for a patient appears twice).
--   wait_minutes    = previous activity COMPLETE -> this activity START  (queue time)
--   service_minutes = this activity START -> this activity COMPLETE      (work time)
{{ config(materialized='table') }}

with ordered as (

    select
        *,
        -- complete sorts before start when timestamps tie, so "finished A, started B
        -- in the same minute" keeps the right order
        row_number() over (
            partition by case_id
            order by
                timestamp,
                case when lifecycle = 'complete' then 0 else 1 end,
                case when activity_name in ('Discharge', 'Admission') then 1 else 0 end
        ) as seq
    from {{ ref('event_log_lifecycle') }}

),

starts as (
    select * from ordered where lifecycle = 'start'
),

completes as (
    select * from ordered where lifecycle = 'complete'
)

select
    s.case_id,
    s.activity_name,
    p.activity_name                                         as prev_activity,
    s.severity,
    s.age_group,
    s.gender,
    s.resource,
    p.timestamp                                             as prev_complete_ts,
    s.timestamp                                             as start_ts,
    c.timestamp                                             as complete_ts,
    timestamp_diff(s.timestamp, p.timestamp, second) / 60.0 as wait_minutes,
    timestamp_diff(c.timestamp, s.timestamp, second) / 60.0 as service_minutes,
    extract(hour from s.timestamp)                          as start_hour
from starts s
join completes c
  on  c.case_id = s.case_id
  and c.seq = s.seq + 1
  and c.activity_name = s.activity_name
join completes p
  on  p.case_id = s.case_id
  and p.seq = s.seq - 1
