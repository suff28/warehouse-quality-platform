select order_id from {{ ref('stg_orders') }} where delivered_at < purchased_at
