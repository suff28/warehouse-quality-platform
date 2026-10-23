select date_key, count(*) line_count, count(distinct order_id) order_count,
cast(sum(net_amount) as decimal(20,2)) net_sales,
cast(sum(freight_amount) as decimal(20,2)) freight_total
from {{ ref('fct_order_items') }} where status != 'cancelled'
group by date_key
