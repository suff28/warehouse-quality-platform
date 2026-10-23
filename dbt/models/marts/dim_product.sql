select product_id, category, list_price from {{ source('raw', 'products') }}
