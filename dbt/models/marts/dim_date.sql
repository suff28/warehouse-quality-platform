select distinct cast(purchased_at as date) date_key,
extract(year from purchased_at) year_number,
extract(month from purchased_at) month_number,
extract(day from purchased_at) day_number
from {{ ref('stg_orders') }}
