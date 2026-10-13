-- One row per patient: total stay, total waiting, and whether they were looped back.
{{ config(materialized='table') }}

with durations as (
    select
        case_id,
        sum(wait_minutes)       as total_wait_min,
        sum(service_minutes)    as total_service_min,
        countif(activity_name = 'Re-Triage') > 0 as had_loop_back,
        any_value(severity)     as severity,
        any_value(age_group)    as age_group,
        any_value(gender)       as gender
    from {{ ref('activity_durations') }}
    group by case_id
),

stay as (
    select
        case_id,
        min(timestamp) as arrival_ts,
        max(timestamp) as exit_ts
    from {{ ref('event_log') }}
    group by case_id
)

select
    s.case_id,
    s.arrival_ts,
    s.exit_ts,
    round(timestamp_diff(s.exit_ts, s.arrival_ts, second) / 60.0, 1) as stay_minutes,
    round(d.total_wait_min, 1)                                      as total_wait_min,
    round(d.total_service_min, 1)                                   as total_service_min,
    d.had_loop_back,
    d.severity,
    d.age_group,
    d.gender
from stay s
join durations d using (case_id)
