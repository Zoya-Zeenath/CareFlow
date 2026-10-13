-- Every patient must end in Discharge or Admission.
select case_id
from {{ ref('event_log') }}
group by case_id
having countif(activity_name in ('Discharge', 'Admission')) = 0
