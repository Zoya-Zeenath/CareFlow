-- One row per distinct patient journey ("variant"), most common first.
-- Answers: what are the common journeys, and which ones are slow?
{{ config(materialized='table') }}

select
    row_number() over (order by count(*) desc, variant_path)  as variant_rank,
    variant_path,
    any_value(steps)                                          as steps,
    count(*)                                                  as patients,
    round(100.0 * count(*) / sum(count(*)) over (), 1)        as pct_of_patients,
    round(avg(stay_minutes), 1)                               as avg_stay_min,
    round(avg(total_wait_min), 1)                             as avg_wait_min,
    logical_or(had_loop_back)                                 as has_loop_back
from {{ ref('case_variants') }}
group by variant_path
