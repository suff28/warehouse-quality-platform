select order_item_key from {{ ref('fct_order_items') }}
where unit_price < 0 or quantity <= 0 or discount_amount < 0 or net_amount < 0
