import argparse
import json
from pathlib import Path

from .generate import bootstrap, generate
from .quality import profile, run_checks


def main():
    p = argparse.ArgumentParser(
        description="Retail warehouse generation and quality gates"
    )
    sub = p.add_subparsers(dest="command", required=True)
    g = sub.add_parser("generate")
    g.add_argument("--orders", type=int, default=10_000_000)
    g.add_argument("--output", type=Path, default=Path("data/scale"))
    g.add_argument("--chunk", type=int, default=1_000_000)
    b = sub.add_parser("bootstrap")
    b.add_argument("--source", type=Path, default=Path("data/scale"))
    b.add_argument("--database", type=Path, default=Path("data/warehouse.duckdb"))
    for name in ["check", "profile"]:
        c = sub.add_parser(name)
        c.add_argument("--database", type=Path, default=Path("data/warehouse.duckdb"))
        c.add_argument("--output", type=Path, default=Path("artifacts/latest"))
        c.add_argument("--config", type=Path, default=Path("config/checks.yml"))
    a = p.parse_args()
    if a.command == "generate":
        print(json.dumps(generate(a.output.resolve(), a.orders, a.chunk), indent=2))
    elif a.command == "bootstrap":
        bootstrap(a.source, a.database)
    else:
        import duckdb

        with duckdb.connect(str(a.database), read_only=True) as con:
            if a.command == "check":
                results = run_checks(con, a.config, a.output)
                print(
                    f"{sum(r['status'] == 'PASS' for r in results)}/{len(results)} passed"
                )
                raise SystemExit(
                    1 if any(r["status"] != "PASS" for r in results) else 0
                )
            else:
                profile(
                    con,
                    [
                        "raw." + t
                        for t in [
                            "customers",
                            "products",
                            "orders",
                            "order_items",
                            "payments",
                            "reviews",
                        ]
                    ],
                    a.output / "profile.json",
                )


if __name__ == "__main__":
    main()
