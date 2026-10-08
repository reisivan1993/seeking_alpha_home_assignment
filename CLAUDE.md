# Seeking Alpha — Senior Data Engineer Home Assignment

Multi-question assignment: written answers (q1, q2, q3, q5) and code (q3_sandbox, q4).

## Project layout

- `q1.md`–`q5.md` — written answers to each question
- `q3_sandbox/` — Docker Compose (Postgres 16 + Python app + Jupyter) for SQL queries
- `q4/` — Python "Set" card-game implementation with pytest suite
- `Senior_Data_Engineer_Home_Assignment_v5.docx.md` — the assignment brief

## Running things

```bash
# q4 tests
cd q4 && python -m pytest -q

# q3 sandbox (Postgres + notebook)
cd q3_sandbox && docker compose up --build
```

## Engineering standards (forge)

- Clean, modular code. Every behaviour change ships with tests.
- Structured logging / metrics on new code paths.
- Every implementation request goes through `/forge:route`.
- See `.harness/config.toml` for gate and runtime commands.
- See `.harness/lessons.md` for accumulated project lessons.
