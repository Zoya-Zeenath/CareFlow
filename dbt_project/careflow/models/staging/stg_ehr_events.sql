-- Staging: standardise names/types, drop unusable rows, remove exact duplicates.
-- One row = one event (a 'start' or 'complete' of an activity for a patient).
{{ config(materialized='view') }}

with source as (

    select * from {{ source('careflow_raw', 'ehr_events_raw') }}

),

cleaned as (

    select
        trim(case_id)                 as case_id,
        trim(activity)                as activity_name,
        lower(trim(lifecycle))        as lifecycle,
        timestamp                     as event_timestamp,
        trim(resource)                as resource,
        severity,
        age_group,
        gender
    from source
    where case_id is not null
      and activity is not null
      and timestamp is not null

),

deduplicated as (

    select distinct * from cleaned

)

select * from deduplicated
