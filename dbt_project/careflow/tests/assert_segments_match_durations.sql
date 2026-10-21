-- The segmented table must contain every activity hand-off exactly once
-- (plus the exit hand-offs). Returns a row (= test fails) if the counts disagree.
select s.segment_total, d.duration_total
from (
    select sum(transitions) as segment_total
    from {{ ref('transition_segments') }}
    where next_activity not in ('Discharge', 'Admission')
) s
cross join (
    select count(*) as duration_total from {{ ref('activity_durations') }}
) d
where s.segment_total != d.duration_total
