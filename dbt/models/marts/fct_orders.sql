{{ config(materialized='incremental', unique_key='order_id', incremental_strategy='delete+insert') }}
-- Filter on arrival batch, never business purchase date: late business events remain eligible.
select o.order_id, o.customer_id, o.status, o.purchased_at, o.updated_at, o.batch_id
from {{ ref('stg_orders') }} o
{% if is_incremental() %}
where o.batch_id >= (select coalesce(max(batch_id),0) from {{ this }})
{% endif %}
