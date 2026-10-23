"""Controlled mutations shared by regression and evidence publishing."""

DEFECTS = [
    (
        "Duplicate order source",
        "create or replace table raw.orders as select * from raw.orders union all select * from raw.orders where order_id=1",
        "orders: source grain uniqueness",
    ),
    (
        "Fan-out doubles revenue",
        "update analytics.mart_daily_sales set net_sales=net_sales*2",
        "Daily net sales reconciliation",
    ),
    (
        "Missing column",
        "alter table analytics.fct_order_items drop column net_amount",
        "Independent line amounts",
    ),
    (
        "Wrong rounding",
        "update analytics.fct_order_items set net_amount=net_amount+0.01 where order_id=1",
        "Independent line amounts",
    ),
    (
        "Missing customer",
        "create or replace table raw.customers as select * from raw.customers where customer_id!=18",
        "orders: customer_id reference",
    ),
    (
        "SCD overlap",
        "insert into analytics.dim_customer select customer_key||'bad',customer_id,customer_name,city,state,valid_from+interval '1 day',null from analytics.dim_customer where customer_id=18",
        "Customer no overlapping intervals",
    ),
    (
        "Replay duplicate",
        "insert into analytics.fct_orders select * from analytics.fct_orders where order_id=1",
        "fct_orders: grain",
    ),
    (
        "Bad chronology",
        "create or replace table raw.orders as select * replace(purchased_at-interval '1 day' as delivered_at) from raw.orders",
        "Delivery chronology",
    ),
    (
        "Negative quantity",
        "create or replace table raw.order_items as select * replace(-1 as quantity) from raw.order_items",
        "Positive quantity",
    ),
    (
        "Missing fact row",
        "delete from analytics.fct_order_items where order_id=1",
        "Fact source count",
    ),
    (
        "Wrong historical key",
        "update analytics.fct_order_items set customer_key=null where order_id=1",
        "Customer historical key required",
    ),
    (
        "Unknown status",
        "create or replace table raw.orders as select * replace('garbage' as status) from raw.orders",
        "Valid status",
    ),
]
