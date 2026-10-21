-- Every hand-off (A -> B) split by patient and staff segments, so Power BI slicers
-- (age group, severity, gender, resource) can filter a process-flow visual.
--
-- IMPORTANT: averages can't be added across slices, so this table stores SUMS and COUNTS.
-- In Power BI compute averages as  DIVIDE(SUM(total_wait_min), SUM(transitions)).
{{ config(materialized='table') }}

with activity_handoffs as (

    -- hand-offs into a step that has a queue and a service time
    select
        case_id,
        prev_activity,
        activity_name   as next_activity,
        age_group,
        severity,
        gender,
        resource        as next_resource,
        wait_minutes,
        service_minutes
    from {{ ref('activity_durations') }}

),

exit_handoffs as (

    -- hand-offs into Discharge / Admission (instant events, no queue or service time),
    -- included so the process flow reaches its end
    select
        case_id,
        lag(activity_name) over (partition by case_id order by event_seq) as prev_activity,
        activity_name   as next_activity,
        age_group,
        severity,
        gender,
        'exit'          as next_resource,
        0.0             as wait_minutes,
        0.0             as service_minutes
    from {{ ref('event_log') }}

),

exits_only as (

    select * from exit_handoffs
    where next_activity in ('Discharge', 'Admission')

),

all_handoffs as (

    select * from activity_handoffs
    union all
    select * from exits_only

)

select
    prev_activity,
    next_activity,
    age_group,
    severity,
    gender,
    next_resource,
    count(*)                              as transitions,
    count(distinct case_id)               as patients,
    round(sum(wait_minutes), 1)           as total_wait_min,
    round(sum(service_minutes), 1)        as total_service_min
from all_handoffs
group by prev_activity, next_activity, age_group, severity, gender, next_resource
