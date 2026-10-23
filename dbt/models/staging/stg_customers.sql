select customer_id, trim(customer_name) customer_name, trim(city) city, upper(trim(state)) state, updated_at, batch_id
from {{ source('raw', 'customers') }}
qualify row_number() over (partition by customer_id order by updated_at desc, batch_id desc) = 1
