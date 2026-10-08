# Q3 sandbox: Postgres + generated test data + notebook

## One command

```bash
cd q3_sandbox
docker compose up --build
```

Then open **http://localhost:8889/lab/tree/q3.ipynb**.

What happens:
1. **db**: Postgres 16 starts.
2. **app**: loads fresh test data, relative to **yesterday (UTC)**, runs the three queries, logs `status=PASSED` or the failed checks, then exits.
3. **notebook**: JupyterLab starts once the data is loaded. Write `%%sql` cells against the database, or run the query files with `run_query("q3a")`.

Stop with `Ctrl+C`. Remove everything with `docker compose down -v`.

## The data

Two schemas, recreated on every `docker compose up`:

| Schema | Contents | Results checked against |
|---|---|---|
| `edge_cases` | 15 users, one per edge case (`app/data.py`) | **Hand-written expected results** + the Python oracle + invariants |
| `full_data` | The edge cases + 5,000 random users (~6K subscriptions, ~110K events), including some bad rows | The Python oracle + invariants |

**Edge cases covered:**
- a subscription starting or ending yesterday;
- events at 00:00:00 and 23:59:59 at both ends of the window;
- anonymous events;
- a user with both products;
- two overlapping subscriptions of the same product, and three mutually overlapping ones;
- a renewal (the next subscription starts on the previous `end_date`);
- zero-length, inverted (end before start) and NULL-start subscriptions;
- subscriptions starting in the future or ending before the window;
- paying without events; active without a subscription;
- an event from a user not in `users`.

**Three kinds of checks:**
- **Hand-written expectations** (`expected_edge_results` in `app/data.py`): what each edge case should produce, worked out by hand.
- **Python oracle** (`app/oracle.py`): the same definitions implemented with plain Python loops, compared with the SQL on all data.
- **Invariants:** rules that must always hold, such as overall ≤ pro + mp, 3b paying = 3a overall, and exactly 30 days returned.

## Other commands

```bash
# re-run the checks after editing a file in queries/ (no rebuild needed)
docker compose run --rm app check

# print a query's result in the terminal
docker compose run --rm app run q3a --schema full_data

# reload with more users or another random seed, then check
docker compose run --rm app all --users 20000 --seed 7

# psql (also reachable from the host on localhost:55432, user/password postgres/postgres, database q3)
docker compose exec db psql -U postgres -d q3
```

## Notes

- **Ports:** 55432 (Postgres) and 8889 (notebook), bound to `localhost` only, to avoid clashing with other local services.
- **No notebook token:** fine for a local sandbox, because the port is reachable only from this machine. Don't expose it on a shared host.
- **Dates move with time:** the data is relative to the day it was loaded. If you leave the stack running past midnight UTC, run `docker compose run --rm app all` again.
