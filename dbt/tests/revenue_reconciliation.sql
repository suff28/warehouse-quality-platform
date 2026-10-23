with expected as (
select cast(sum(i.quantity*i.unit_price-i.discount_amount) as decimal(20,2)) amount
from {{ source('raw','order_items') }} i join {{ ref('stg_orders') }} o on i.order_id=o.order_id
where o.status != 'cancelled'), actual as (select sum(net_sales) amount from {{ ref('mart_daily_sales') }})
select expected.amount expected, actual.amount actual from expected cross join actual
where expected.amount != actual.amount
