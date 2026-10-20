-- One row per patient: the exact path they took, written as one string.
-- e.g. "Arrival > Registration > Triage > Doctor Consultation > X-Ray > Treatment > Discharge"
{{ config(materialized='table') }}

with paths as (

    select
        case_id,
        string_agg(activity_name, ' > ' order by event_seq) as variant_path,
        count(*)                                            as steps
    from {{ ref('event_log') }}
    group by case_id

)

select
    p.case_id,
    p.variant_path,
    p.steps,
    c.stay_minutes,
    c.total_wait_min,
    c.had_loop_back,
    c.severity,
    c.age_group,
    c.gender
from paths p
join {{ ref('case_summary') }} c using (case_id)
