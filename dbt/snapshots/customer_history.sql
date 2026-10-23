{% snapshot customer_history %}
{{ config(target_schema='analytics', unique_key='customer_id', strategy='timestamp', updated_at='updated_at') }}
select customer_id, customer_name, city, state, updated_at from {{ ref('stg_customers') }}
{% endsnapshot %}
