select cast(i.order_id as varchar) || '-' || cast(i.line_id as varchar) order_item_key,
i.order_id, i.line_id, o.customer_id, c.customer_key, i.product_id, i.seller_id,
cast(o.purchased_at as date) date_key, o.status, i.quantity, i.unit_price, i.discount_amount,
cast(i.quantity * i.unit_price - i.discount_amount as decimal(18,2)) net_amount,
i.freight_amount, o.updated_at, i.batch_id
from {{ source('raw', 'order_items') }} i
join {{ ref('stg_orders') }} o on i.order_id = o.order_id
left join {{ ref('dim_customer') }} c on o.customer_id=c.customer_id
and o.purchased_at >= c.valid_from and (o.purchased_at < c.valid_to or c.valid_to is null)
