-- Small cloud integration delivery; internal stage route, not direct S3 loading.

USE ROLE ACCOUNTADMIN;

USE WAREHOUSE RETAIL_QE_WH;

USE DATABASE RETAIL_QE;

USE SCHEMA RAW;

CREATE TABLE IF NOT EXISTS RETAIL_QE.RAW.customers (
  customer_id BIGINT,
  customer_name VARCHAR(500),
  city VARCHAR(500),
  state VARCHAR(500),
  updated_at TIMESTAMP_NTZ,
  batch_id BIGINT
);

COPY INTO RETAIL_QE.RAW.customers
FROM @RETAIL_QE.RAW.LOCAL_DELIVERY
PATTERN = '.*customers[.]parquet'
FILE_FORMAT = (TYPE = PARQUET USE_LOGICAL_TYPE = TRUE)
MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE
ON_ERROR = ABORT_STATEMENT;

CREATE TABLE IF NOT EXISTS RETAIL_QE.RAW.orders (
  order_id BIGINT,
  customer_id BIGINT,
  purchased_at TIMESTAMP_NTZ,
  delivered_at TIMESTAMP_NTZ,
  status VARCHAR(500),
  updated_at TIMESTAMP_NTZ,
  batch_id BIGINT
);

COPY INTO RETAIL_QE.RAW.orders
FROM @RETAIL_QE.RAW.LOCAL_DELIVERY
PATTERN = '.*orders[.]parquet'
FILE_FORMAT = (TYPE = PARQUET USE_LOGICAL_TYPE = TRUE)
MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE
ON_ERROR = ABORT_STATEMENT;

CREATE TABLE IF NOT EXISTS RETAIL_QE.RAW.products (
  product_id BIGINT,
  category VARCHAR(500),
  list_price DECIMAL(18,2)
);

COPY INTO RETAIL_QE.RAW.products
FROM @RETAIL_QE.RAW.LOCAL_DELIVERY
PATTERN = '.*products[.]parquet'
FILE_FORMAT = (TYPE = PARQUET USE_LOGICAL_TYPE = TRUE)
MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE
ON_ERROR = ABORT_STATEMENT;

CREATE TABLE IF NOT EXISTS RETAIL_QE.RAW.sellers (
  seller_id BIGINT,
  seller_name VARCHAR(500),
  state VARCHAR(500)
);

COPY INTO RETAIL_QE.RAW.sellers
FROM @RETAIL_QE.RAW.LOCAL_DELIVERY
PATTERN = '.*sellers[.]parquet'
FILE_FORMAT = (TYPE = PARQUET USE_LOGICAL_TYPE = TRUE)
MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE
ON_ERROR = ABORT_STATEMENT;

CREATE TABLE IF NOT EXISTS RETAIL_QE.RAW.order_items (
  order_id BIGINT,
  line_id BIGINT,
  product_id BIGINT,
  seller_id BIGINT,
  quantity BIGINT,
  unit_price DECIMAL(18,2),
  discount_amount DECIMAL(18,2),
  freight_amount DECIMAL(18,2),
  batch_id BIGINT
);

COPY INTO RETAIL_QE.RAW.order_items
FROM @RETAIL_QE.RAW.LOCAL_DELIVERY
PATTERN = '.*order_items[.]parquet'
FILE_FORMAT = (TYPE = PARQUET USE_LOGICAL_TYPE = TRUE)
MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE
ON_ERROR = ABORT_STATEMENT;

CREATE TABLE IF NOT EXISTS RETAIL_QE.RAW.payments (
  order_id BIGINT,
  payment_sequence BIGINT,
  payment_method VARCHAR(500),
  payment_amount DECIMAL(18,2),
  batch_id BIGINT
);

COPY INTO RETAIL_QE.RAW.payments
FROM @RETAIL_QE.RAW.LOCAL_DELIVERY
PATTERN = '.*payments[.]parquet'
FILE_FORMAT = (TYPE = PARQUET USE_LOGICAL_TYPE = TRUE)
MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE
ON_ERROR = ABORT_STATEMENT;

CREATE TABLE IF NOT EXISTS RETAIL_QE.RAW.reviews (
  review_id BIGINT,
  order_id BIGINT,
  score BIGINT,
  review_text VARCHAR(500),
  batch_id BIGINT
);

COPY INTO RETAIL_QE.RAW.reviews
FROM @RETAIL_QE.RAW.LOCAL_DELIVERY
PATTERN = '.*reviews[.]parquet'
FILE_FORMAT = (TYPE = PARQUET USE_LOGICAL_TYPE = TRUE)
MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE
ON_ERROR = ABORT_STATEMENT;

SELECT 'customers' AS table_name, 2000 AS expected_rows, COUNT(*) AS actual_rows, IFF(COUNT(*) = 2000, 'PASS', 'FAIL') AS status FROM RETAIL_QE.RAW.customers
UNION ALL
SELECT 'orders' AS table_name, 10000 AS expected_rows, COUNT(*) AS actual_rows, IFF(COUNT(*) = 10000, 'PASS', 'FAIL') AS status FROM RETAIL_QE.RAW.orders
UNION ALL
SELECT 'products' AS table_name, 100 AS expected_rows, COUNT(*) AS actual_rows, IFF(COUNT(*) = 100, 'PASS', 'FAIL') AS status FROM RETAIL_QE.RAW.products
UNION ALL
SELECT 'sellers' AS table_name, 10 AS expected_rows, COUNT(*) AS actual_rows, IFF(COUNT(*) = 10, 'PASS', 'FAIL') AS status FROM RETAIL_QE.RAW.sellers
UNION ALL
SELECT 'order_items' AS table_name, 30000 AS expected_rows, COUNT(*) AS actual_rows, IFF(COUNT(*) = 30000, 'PASS', 'FAIL') AS status FROM RETAIL_QE.RAW.order_items
UNION ALL
SELECT 'payments' AS table_name, 20000 AS expected_rows, COUNT(*) AS actual_rows, IFF(COUNT(*) = 20000, 'PASS', 'FAIL') AS status FROM RETAIL_QE.RAW.payments
UNION ALL
SELECT 'reviews' AS table_name, 3333 AS expected_rows, COUNT(*) AS actual_rows, IFF(COUNT(*) = 3333, 'PASS', 'FAIL') AS status FROM RETAIL_QE.RAW.reviews
ORDER BY table_name;
