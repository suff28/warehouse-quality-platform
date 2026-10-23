"""Assemble an auditable delivery from relational extracts, CSV, and file sources."""

import argparse
import hashlib
import json
import shutil
from pathlib import Path

import duckdb


def assemble(original: Path, extracted: Path, output: Path):
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True)
    con = duckdb.connect()
    records = []
    for table in [
        "customers",
        "products",
        "sellers",
        "orders",
        "order_items",
        "payments",
        "reviews",
    ]:
        dest = output / table
        dest.mkdir()
        if table == "payments":
            csv = original / "payments_csv/payments.csv"
            con.execute(
                f"COPY (select * from read_csv('{csv.resolve().as_posix()}',header=true,columns={{'order_id':'BIGINT','payment_sequence':'BIGINT','payment_method':'VARCHAR','payment_amount':'DECIMAL(18,2)','batch_id':'BIGINT'}})) TO '{(dest / 'part-000.parquet').resolve().as_posix()}' (FORMAT PARQUET,COMPRESSION ZSTD)"
            )
            provenance = "csv"
        else:
            relational = table in ["customers", "products", "sellers", "orders"]
            source = (extracted if relational else original) / table
            files = list(source.glob("*.parquet"))
            if not files:
                raise FileNotFoundError(source)
            for file in files:
                shutil.copy2(file, dest / file.name)
            provenance = "relational-extract" if relational else "parquet-file"
        for file in dest.glob("*.parquet"):
            with file.open("rb") as h:
                digest = hashlib.file_digest(h, "sha256").hexdigest()
            count = con.execute(
                f"select count(*) from read_parquet('{file.resolve().as_posix()}')"
            ).fetchone()[0]
            records.append(
                dict(
                    table=table,
                    path=str(file.relative_to(output)),
                    rows=count,
                    sha256=digest,
                    source=provenance,
                )
            )
    (output / "manifest.json").write_text(json.dumps(records, indent=2))
    con.close()
    return records


def compare(left: Path, right: Path):
    """Exact relational multiset equality, including nulls and duplicate multiplicity."""
    con = duckdb.connect()
    results = []
    for table in ["customers", "products", "sellers", "orders"]:
        a = f"select * from read_parquet('{(left / table).resolve().as_posix()}/*.parquet')"
        b = f"select * from read_parquet('{(right / table).resolve().as_posix()}/*.parquet')"
        missing = con.execute(
            f"select count(*) from (({a}) except all ({b})) x"
        ).fetchone()[0]
        extra = con.execute(
            f"select count(*) from (({b}) except all ({a})) x"
        ).fetchone()[0]
        results.append(
            dict(
                table=table,
                missing=missing,
                extra=extra,
                status="PASS" if missing + extra == 0 else "FAIL",
            )
        )
    con.close()
    return results


def main():
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=["assemble", "compare"])
    p.add_argument("--original", type=Path, default=Path("data/smoke"))
    p.add_argument("--extracted", type=Path, default=Path("data/postgres-extracted"))
    p.add_argument("--output", type=Path, default=Path("data/delivery"))
    a = p.parse_args()
    results = (
        assemble(a.original, a.extracted, a.output)
        if a.action == "assemble"
        else compare(a.original, a.extracted)
    )
    Path("artifacts").mkdir(exist_ok=True)
    Path("artifacts/" + a.action + ".json").write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))
    if any(r.get("status") == "FAIL" for r in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
