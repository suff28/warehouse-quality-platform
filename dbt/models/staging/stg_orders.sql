select order_id, customer_id, purchased_at, delivered_at, lower(trim(status)) status, updated_at, batch_id
from {{ source('raw', 'orders') }}
qualify row_number() over (partition by order_id order by updated_at desc, batch_id desc) = 1
