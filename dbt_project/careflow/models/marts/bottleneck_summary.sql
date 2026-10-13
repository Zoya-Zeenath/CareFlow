-- Ranks activities by TOTAL time patients lose waiting for them.
-- total_wait_hours = avg wait x volume, so a slow-but-rare step doesn't outrank
-- a moderately slow step that everyone passes through.
{{ config(materialized='table') }}

select
    activity_name,
    count(*)                                                   as visits,
    round(avg(wait_minutes), 1)                                as avg_wait_min,
    round(approx_quantiles(wait_minutes, 100)[offset(90)], 1)  as p90_wait_min,
    round(avg(service_minutes), 1)                             as avg_service_min,
    round(sum(wait_minutes) / 60.0, 1)                         as total_wait_hours,
    rank() over (order by sum(wait_minutes) desc)              as bottleneck_rank
from {{ ref('activity_durations') }}
group by activity_name
