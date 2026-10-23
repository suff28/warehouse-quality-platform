SHELL := /bin/bash
PY := .venv/bin/python
DBT := .venv/bin/dbt
export PYTHONPATH := src
export DBT_SEND_ANONYMOUS_USAGE_STATS := false
export WAREHOUSE_DB := $(CURDIR)/data/warehouse.duckdb
.PHONY: install smoke scale regression quality profile defects docs cloud-check
install:
	python3.11 -m venv .venv
	.venv/bin/pip install '.[dev]'
smoke:
	@test -f data/smoke/manifest.json || $(PY) -m warehouse_qe.cli generate --orders 10000 --output data/smoke > artifacts/generation-smoke.log
	$(PY) -m warehouse_qe.cli bootstrap --source data/smoke
	$(DBT) build --project-dir dbt --profiles-dir dbt
	$(PY) -m warehouse_qe.cli check --output artifacts/smoke
scale:
	@test -f data/scale/manifest.json || $(PY) -m warehouse_qe.cli generate --orders 10000000 --output data/scale > artifacts/generation-scale.log
	$(PY) -m warehouse_qe.cli bootstrap --source data/scale --database data/scale.duckdb
	WAREHOUSE_DB='$(CURDIR)/data/scale.duckdb' $(DBT) build --project-dir dbt --profiles-dir dbt --target-path target-scale --log-path logs-scale
	$(PY) -m warehouse_qe.cli check --database data/scale.duckdb --output artifacts/scale
	$(PY) -m warehouse_qe.cli profile --database data/scale.duckdb --output artifacts/scale
regression:
	.venv/bin/pytest -q --html=artifacts/pytest.html --self-contained-html
quality:
	$(PY) -m warehouse_qe.cli check
profile:
	$(PY) -m warehouse_qe.cli profile
defects:
	$(PY) -m warehouse_qe.defects
docs:
	$(DBT) docs generate --project-dir dbt --profiles-dir dbt
cloud-check:
	$(PY) -m warehouse_qe.cloud check
