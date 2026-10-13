-- A patient can't start an activity before finishing the previous one.
select case_id, activity_name, wait_minutes
from {{ ref('activity_durations') }}
where wait_minutes < 0 or service_minutes <= 0
