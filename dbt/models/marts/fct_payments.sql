-- Aggregate at order grain before joining payments to orders or order lines.
select order_id, count(*) payment_count, cast(sum(payment_amount) as decimal(20,2)) paid_amount
from {{ source('raw', 'payments') }} group by order_id
