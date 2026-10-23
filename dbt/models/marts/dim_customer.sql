select dbt_scd_id customer_key, customer_id, customer_name, city, state,
       dbt_valid_from valid_from, dbt_valid_to valid_to
from {{ ref('customer_history') }}
