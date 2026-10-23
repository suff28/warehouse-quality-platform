select customer_id, valid_from, valid_to from (
select *, lead(valid_from) over(partition by customer_id order by valid_from) next_start
from {{ ref('dim_customer') }}) t
where valid_to <= valid_from or (next_start is not null and (valid_to is null or valid_to > next_start))
