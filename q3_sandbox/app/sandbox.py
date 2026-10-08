"""Seed a Postgres database with Q3 test data and check the queries against it.

Two schemas are created:
  edge_cases  one user per edge case; results are compared with hand-written expectations
  full_data   the edge cases plus random users; results are compared with the Python oracle

Commands:
  seed   [--users N] [--seed S]   (re)create both schemas with fresh data
  check                           run q3a/q3b/q3c on both schemas and verify the results
  run    q3a|q3b|q3c [--schema S] print a query's result
  all    [--users N] [--seed S]   seed, then check (the default in docker compose)
  --report-only (check/all)       log failed checks but exit 0
"""

import argparse
import logging
import os
import sys
from datetime import date, timedelta
from pathlib import Path

import psycopg

import oracle
from data import Dataset, Event, Subscription, edge_cases, expected_edge_results, random_data

QUERIES_DIR = Path(os.environ.get("QUERIES_DIR", "/queries"))
SQL_DIR = Path(os.environ.get("SQL_DIR", "/sql"))
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:55432/q3")
SCHEMAS = ("edge_cases", "full_data")
QUERIES = ("q3a", "q3b", "q3c")
MAX_DIFFS_SHOWN = 5

log = logging.getLogger("q3_sandbox")


# ---------- database ----------

def connect(schema: str) -> psycopg.Connection:
    conn = psycopg.connect(DATABASE_URL, autocommit=True)
    conn.execute("SET TIME ZONE 'UTC'")
    conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
    conn.execute(f"SET search_path TO {schema}")
    return conn


def yesterday(conn: psycopg.Connection) -> date:
    return conn.execute("SELECT CURRENT_DATE - 1").fetchone()[0]


def load(conn: psycopg.Connection, dataset: Dataset) -> None:
    conn.execute((SQL_DIR / "schema.sql").read_text())
    with conn.cursor() as cur:
        with cur.copy("COPY users (user_id) FROM STDIN") as copy:
            for user in dataset.users:
                copy.write_row((user,))
        with cur.copy("COPY subscriptions (subscription_id, user_id, product, start_date, end_date) FROM STDIN") as copy:
            for s in dataset.subscriptions:
                copy.write_row((s.subscription_id, s.user_id, s.product, s.start_date, s.end_date))
        with cur.copy("COPY events (event_ts, user_id, event_name) FROM STDIN") as copy:
            for e in dataset.events:
                copy.write_row((e.event_ts, e.user_id, e.event_name))


def read_back(conn: psycopg.Connection) -> tuple[list[Subscription], list[Event]]:
    subs = [Subscription(*r) for r in conn.execute(
        "SELECT subscription_id, user_id, product, start_date, end_date FROM subscriptions")]
    events = [Event(*r) for r in conn.execute("SELECT event_ts, user_id, event_name FROM events")]
    return subs, events


def run_query(conn: psycopg.Connection, name: str) -> tuple[list[str], list[tuple]]:
    cur = conn.execute((QUERIES_DIR / f"{name}.sql").read_text())
    return [c.name for c in cur.description], cur.fetchall()


# ---------- seed ----------

def seed(n_users: int, rng_seed: int) -> None:
    with connect("edge_cases") as conn:
        day = yesterday(conn)
        edge = edge_cases(day)
        load(conn, edge)
        log.info("event=seeded schema=edge_cases yesterday=%s users=%d subscriptions=%d events=%d",
                 day, len(edge.users), len(edge.subscriptions), len(edge.events))

    with connect("full_data") as conn:
        bulk = random_data(day, n_users, rng_seed, first_subscription_id=len(edge.subscriptions) + 1)
        full = Dataset(edge.users + bulk.users, edge.subscriptions + bulk.subscriptions, edge.events + bulk.events)
        load(conn, full)
        log.info("event=seeded schema=full_data yesterday=%s users=%d subscriptions=%d events=%d seed=%d",
                 day, len(full.users), len(full.subscriptions), len(full.events), rng_seed)


# ---------- check ----------

class Report:
    def __init__(self) -> None:
        self.failures = 0

    def result(self, schema: str, check: str, problems: list[str]) -> None:
        if problems:
            self.failures += 1
            log.error("event=check_failed schema=%s check=%s problems=%d", schema, check, len(problems))
            for p in problems[:MAX_DIFFS_SHOWN]:
                log.error("event=check_detail schema=%s check=%s detail=%r", schema, check, p)
        else:
            log.info("event=check_passed schema=%s check=%s", schema, check)


def compare(actual: list[tuple], expected: list[tuple]) -> list[str]:
    """Compare as sorted lists, so the database's text collation doesn't matter."""
    a, e = sorted(actual, key=repr), sorted(expected, key=repr)
    if a == e:
        return []
    missing = [f"expected but not returned: {row}" for row in e if row not in a]
    extra = [f"returned but not expected: {row}" for row in a if row not in e]
    return missing + extra


def hand_expected_rows(day: date) -> dict[str, list[tuple]]:
    exp = expected_edge_results(day)
    days = oracle.window(day)
    q3a = [(d, *exp["q3a"].get(d, (0, 0, 0))) for d in days]
    q3b = []
    for d in days:
        active, paying = exp["q3b"].get(d, (0, 0))
        q3b.append((d, active, paying, oracle.percentage(paying, active)))
    return {"q3a": q3a, "q3b": q3b, "q3c": exp["q3c"]}


def as_pairs(rows: list[tuple]) -> list[tuple]:
    """Reduce 3c rows to (user, id_1, id_2, same_product, overlap_start, overlap_end)."""
    return [(r[0], r[1], r[5], r[9], r[10], r[11]) for r in rows]


def invariant_problems(day: date, q3a: list[tuple], q3b: list[tuple], q3c: list[tuple]) -> list[str]:
    problems = []
    days = oracle.window(day)
    for name, rows in (("q3a", q3a), ("q3b", q3b)):
        if [r[0] for r in rows] != days:
            problems.append(f"{name} must return the 30 days ending yesterday, in order")
    for d, overall, pro, mp in q3a:
        if not max(pro, mp) <= overall <= pro + mp:
            problems.append(f"{d}: overall={overall} must be between max(pro, mp) and pro + mp ({pro}, {mp})")
    overall_by_day = {r[0]: r[1] for r in q3a}
    for d, active, paying, pct in q3b:
        if paying != overall_by_day.get(d):
            problems.append(f"{d}: 3b paying={paying} must equal 3a overall={overall_by_day.get(d)}")
        if paying > active:
            problems.append(f"{d}: paying={paying} > active={active}")
        if (pct is None) != (active == 0) or (pct is not None and not 0 <= pct <= 100):
            problems.append(f"{d}: bad percentage {pct} for active={active}")
    for r in q3c:
        if not r[1] < r[5]:
            problems.append(f"3c pair {r[1]},{r[5]} must have id_1 < id_2")
        if r[11] is not None and not r[10] < r[11]:
            problems.append(f"3c pair {r[1]},{r[5]}: overlap_start must be before overlap_end")
    return problems


def run_all_queries(conn: psycopg.Connection, schema: str, report: Report) -> dict[str, list[tuple]] | None:
    """Run every query; a query that errors (e.g. on bad data) is a failed check, not a crash."""
    results = {}
    for q in QUERIES:
        try:
            results[q] = run_query(conn, q)[1]
        except psycopg.Error as exc:
            report.result(schema, f"{q}_runs", [f"{type(exc).__name__}: {str(exc).strip()}"])
    return results if len(results) == len(QUERIES) else None


def check() -> int:
    report = Report()
    for schema in SCHEMAS:
        with connect(schema) as conn:
            day = yesterday(conn)
            results = run_all_queries(conn, schema, report)
            subs, events = read_back(conn)
        if results is None:
            continue

        oracle_rows = {
            "q3a": oracle.expected_3a(subs, events, day),
            "q3b": oracle.expected_3b(subs, events, day),
            "q3c": oracle.expected_3c(subs),
        }
        for q in QUERIES:
            report.result(schema, f"{q}_matches_oracle", compare(results[q], oracle_rows[q]))

        if schema == "edge_cases":
            hand = hand_expected_rows(day)
            report.result(schema, "q3a_matches_hand_expected", compare(results["q3a"], hand["q3a"]))
            report.result(schema, "q3b_matches_hand_expected", compare(results["q3b"], hand["q3b"]))
            hand_pairs = [(*k, *v) for k, v in hand["q3c"].items()]
            report.result(schema, "q3c_matches_hand_expected", compare(as_pairs(results["q3c"]), hand_pairs))

        report.result(schema, "invariants", invariant_problems(day, results["q3a"], results["q3b"], results["q3c"]))

    if report.failures:
        log.error("event=check_summary status=FAILED failed_checks=%d", report.failures)
        return 1
    log.info("event=check_summary status=PASSED")
    return 0


# ---------- run ----------

def print_table(columns: list[str], rows: list[tuple]) -> None:
    cells = [["" if v is None else str(v) for v in r] for r in rows]
    widths = [max([len(c)] + [len(r[i]) for r in cells]) for i, c in enumerate(columns)]
    line = " | ".join(c.ljust(w) for c, w in zip(columns, widths))
    sys.stdout.write(line + "\n" + "-+-".join("-" * w for w in widths) + "\n")
    for r in cells:
        sys.stdout.write(" | ".join(v.ljust(w) for v, w in zip(r, widths)) + "\n")
    sys.stdout.write(f"({len(rows)} rows)\n")


def run(name: str, schema: str) -> None:
    with connect(schema) as conn:
        columns, rows = run_query(conn, name)
    print_table(columns, rows)


# ---------- cli ----------

def main() -> int:
    logging.basicConfig(level=logging.INFO, format="ts=%(asctime)s level=%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    for cmd in ("seed", "all"):
        p = sub.add_parser(cmd)
        p.add_argument("--users", type=int, default=5000, help="number of random users in full_data")
        p.add_argument("--seed", type=int, default=42, help="random seed, for reproducible data")
    for cmd in ("check", "all"):
        p = sub.choices[cmd] if cmd in sub.choices else sub.add_parser(cmd)
        p.add_argument("--report-only", action="store_true",
                       help="log failed checks but exit 0 (so the notebook still starts)")
    p_run = sub.add_parser("run")
    p_run.add_argument("query", choices=QUERIES)
    p_run.add_argument("--schema", choices=SCHEMAS, default="edge_cases")
    args = parser.parse_args()

    if args.command in ("seed", "all"):
        if args.users < 0:
            parser.error("--users must be 0 or more")
        seed(args.users, args.seed)
    if args.command in ("check", "all"):
        status = check()
        return 0 if args.report_only else status
    if args.command == "run":
        run(args.query, args.schema)
    return 0


if __name__ == "__main__":
    sys.exit(main())
