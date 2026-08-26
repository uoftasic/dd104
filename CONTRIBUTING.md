# Contributing

Thanks for improving materials for the **UofT ASIC Team**.

## After creating a course from this template

1. Run `scripts/init-template.py` with `--id`, `--title`, and `--description` (org is always `uoftasic`).
2. Enable GitHub Pages: branch `main`, folder `/docs`.
3. Prefer repo names that match course ids (`dd103`, `ic101`, …).

See [TEMPLATE.md](TEMPLATE.md).

## Placeholders

Only these three are fillable:

| Token | Example |
|-------|---------|
| `dd104` | `dd103` |
| `DD104 — Pre-Silicon Verification` | `DD103 — RTL on FPGAs & ASICs` |
| `Verilator and cocotb: find the bugs hiding in a real 8-bit core.` | `RTL synthesis intro with Yosys` |

## Conventions

| Item | Convention |
|------|------------|
| Org | `uoftasic` |
| Default branch | `main` |
| Docs pages | kebab-case `.md` under `docs/` |
| Lab IDs | `lab-NN-short-name` |
| Adding a doc page | add `.md` under `docs/`, link in `docs/_sidebar.md` |
| Adding a lab | `labs/<id>/` + `docs/labs/<id>-overview.md` + sidebar entry |
| Binaries | small images in `docs/assets/`; large data → Git LFS or external |

## Docs vs labs

- **`docs/`** — published site. Lab *writeups* in `docs/labs/`.
- **`labs/`** — runnable HDL / Python / data. Each `labs/<id>/README.md` links to its Docsify writeup.
- **`scripts/`** — utilities; list entry points in `scripts/README.md`.

Do not put grades, solution keys, or PII under `docs/`. Prefer `labs/**/solutions/` and gitignore them on student forks when needed.

## Before you touch a checker

Every verdict in DD104 — `labs/common/check.py`, `labs/*/check.py`, `labs/*/hunt.py` — reads
`labs/common/verdict.py` for the one distinction the whole course rests on: *the assertion
fired* (the design is at fault) versus *the test blew up* (the testbench is). Do not re-derive
that in a checker. Import it.

```bash
cd labs/common
make selftest            # the classifier and a source audit. Under a second.
make selftest FULL=1     # ... and every checker in the course, end to end. Minutes.
```

`make selftest` fails if any checker grows its own `class Result`, its own `ET.parse`, or a
`findall("error")` — cocotb 2.x never writes an `<error>` element, so that last one is dead
code that looks like a safety net. `FULL=1` points every checker at a deliberately broken
testbench and reads what it says. See [`labs/common/selftest/README.md`](labs/common/selftest/README.md).

A grader that says PASS when it did nothing is worse than no grader at all, and DD104 has
shipped two of those.

## Local docs preview

```bash
npx docsify-cli serve docs
```

## Pull requests

Keep changes focused. For doc-only PRs, check navigation and math locally when practical. Optional CI may link-check `docs/**`.
