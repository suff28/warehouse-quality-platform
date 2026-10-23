select customer_id from {{ ref('dim_customer') }} group by customer_id
having sum(case when valid_to is null then 1 else 0 end) != 1
