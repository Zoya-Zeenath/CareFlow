-- Every patient must belong to exactly one variant.
-- Returns a row (= test fails) if the totals don't match.
select v.total_in_variants, c.total_patients
from (select sum(patients) as total_in_variants from {{ ref('variant_summary') }}) v
cross join (select count(*) as total_patients from {{ ref('case_summary') }}) c
where v.total_in_variants != c.total_patients
