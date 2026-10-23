select seller_id, seller_name, state from {{ source('raw', 'sellers') }}
