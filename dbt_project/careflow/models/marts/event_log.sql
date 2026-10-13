-- The process-mining "Event Log": exactly Case_ID, Activity_Name, Timestamp
-- (plus case attributes for dashboard filters).
-- We keep 'complete' events: one row per finished activity, in time order.
{{ config(materialized='table') }}

select
    case_id,
    activity_name,
    event_timestamp                                             as timestamp,
    resource,
    severity,
    age_group,
    gender,
    row_number() over (
        partition by case_id
        order by
            event_timestamp,
            -- Treatment completes and Discharge is logged at the same instant:
            -- exit events must always sort last
            case when activity_name in ('Discharge', 'Admission') then 1 else 0 end
    )                                                           as event_seq
from {{ ref('stg_ehr_events') }}
where lifecycle = 'complete'
