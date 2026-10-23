-- Each split payment rounds independently, so allow one cent per order.
select p.order_id from {{ ref('fct_payments') }} p join (
select order_id, sum(net_amount+freight_amount) expected from {{ ref('fct_order_items') }} group by order_id
) i on p.order_id=i.order_id where abs(p.paid_amount-i.expected) > 0.01
