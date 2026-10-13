-- Singular test: returns rows that BREAK the rule "nothing happens before arrival".
-- dbt fails the test if this query returns any rows.
with arrival as (
    select case_id, timestamp as arrival_ts
    from {{ ref('event_log') }}
    where activity_name = 'Arrival'
)
select e.case_id, e.activity_name, e.timestamp, a.arrival_ts
from {{ ref('event_log') }} e
join arrival a using (case_id)
where e.timestamp < a.arrival_ts
