-- Average time for every hand-off in the process (node -> node),
-- e.g. Triage -> Doctor Consultation, Doctor Consultation -> X-Ray.
{{ config(materialized='table') }}

select
    prev_activity,
    activity_name                                              as next_activity,
    count(*)                                                   as patients,
    round(avg(wait_minutes), 1)                                as avg_wait_min,
    round(approx_quantiles(wait_minutes, 100)[offset(90)], 1)  as p90_wait_min,
    round(avg(service_minutes), 1)                             as avg_service_min,
    round(avg(wait_minutes + service_minutes), 1)              as avg_transition_min
from {{ ref('activity_durations') }}
group by prev_activity, activity_name
