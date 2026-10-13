-- Start + complete events together. Used in Week 3 to separate
-- QUEUE WAIT (previous complete -> next start) from SERVICE TIME (start -> complete).
{{ config(materialized='table') }}

select
    case_id,
    activity_name,
    lifecycle,
    event_timestamp as timestamp,
    resource,
    severity,
    age_group,
    gender
from {{ ref('stg_ehr_events') }}
