# Contributing

Thanks for improving materials for the UofT ASIC Team.

## After creating a course from this template

1. Run `scripts/init-template.py` with `--id`, `--title`, and `--description` (org is always `uoftasic`).
2. Enable GitHub Pages with Source: GitHub Actions. `.github/workflows/site.yml` builds `docs/` with Quarto and deploys it.
3. Prefer repo names that match course ids (`dd103`, `ic101`, …).

See [TEMPLATE.md](TEMPLATE.md).

## Placeholders

Only these three are fillable:

| Token | Example |
|-------|---------|
| `dd104` | `dd103` |
| `DD104 — Pre-Silicon Verification` | `DD103 — RTL on FPGAs & ASICs` |
| `Write cocotb tests that catch all thirteen broken versions of SimProc, an 8-bit processor written by students on the team.` | `RTL synthesis intro with Yosys` |

## Conventions

| Item | Convention |
|------|------------|
| Org | `uoftasic` |
| Default branch | `main` |
| Docs pages | kebab-case `.md` under `docs/` |
| Lab IDs | `lab-NN-short-name` |
| Adding a doc page | add `.md` under `docs/`, add it to the sidebar in `docs/_quarto.yml` and the chapters in `docs/_quarto-pdf.yml` |
| Adding a lab | `labs/<id>/` + `docs/labs/<id>-overview.md` + a Course path row in `docs/index.md` + sidebar entry in `docs/_quarto.yml` (and a chapter in `docs/_quarto-pdf.yml`) in the same order |
| Links between pages | relative to the page they are written in (`../guide/x.md` from a lab) |
| Binaries | small images in `docs/assets/`; large data → Git LFS or external |

## Docs and labs

- `docs/`: the published site. The home page, `docs/index.md`, holds the Course path table, which
  alternates Read rows (guide pages) and Do rows (one lab each) under the columns
  `| # | | What | Time |`. Read and Do are plain text; a Do row links `Lab NN: Title` and ends
  with one sentence on what you'll do. The row times add up to the total on the home page. Keep
  the sidebar in `docs/_quarto.yml` and the chapters in `docs/_quarto-pdf.yml` in the same order,
  with the same lab names.
- `docs/guide/`: reading only. Concepts, figures, worked examples and their output. No commands
  the student has to run; point to the lab part where they run it instead. Short "Check yourself"
  questions go at the end of the page.
- `docs/labs/`: lab writeups, the only place students are told to run things. Title
  `# Lab NN: Title`. Shape: what you'll build (2–3 lines), time, before you start, numbered parts
  of numbered steps, each part opening with the question it answers and ending in a "Check:", and
  Finishing. Questions sit at the step where they arise, with the answer in a collapsed
  `<details>` block; optional parts go last, marked "(optional)". Finishing is "You're done when"
  (one checkable line about the student's own work), then Questions (each with a collapsed answer
  or a pointer to its step), then Submit (or nothing). Going further (optional) and a "Next on the
  Course path" line come after it.
- `docs/reference/`: lookup pages (tables, short entries).
- `labs/`: runnable HDL, Python and data. Each `labs/<id>/README.md` links to its writeup and
  lists how to run it, its make targets and its files, without repeating the writeup's teaching.
- `scripts/`: utilities; list entry points in `scripts/README.md`.

Do not put grades, solution keys, or PII under `docs/`. Prefer `labs/**/solutions/` and gitignore them on student forks when needed.

## Before you touch a checker

Every verdict in DD104 (`labs/common/check.py`, `labs/*/check.py`, `labs/*/hunt.py`) reads
`labs/common/verdict.py` for the distinction the whole course rests on: *the assertion fired*,
which means the design is at fault, against *the test blew up*, which means the testbench is.
Don't reimplement that in a checker; import it, so that every checker draws the line in the same
place.

```bash
cd labs/common
make selftest            # the classifier and a source audit. Under a second.
make selftest FULL=1     # ... and every checker in the course, end to end. Minutes.
```

`make selftest` fails if any checker has its own `class Result`, its own `ET.parse`, or a
`findall("error")`. cocotb 2.x never writes an `<error>` element, so a check for one looks like a
safety net but can never run. `FULL=1` points every checker at a deliberately broken testbench and
reads what it says. See [`labs/common/selftest/README.md`](labs/common/selftest/README.md).

A grader that says PASS when it did nothing is worse than no grader, and DD104 has shipped two.

## Local docs preview

```bash
quarto preview docs
```

## Pull requests

Keep changes focused. For doc-only PRs, check navigation and math in the local preview when you
can. Two workflows check `docs/**` on pull requests: `.github/workflows/docs-link-check.yml` runs
lychee over the Markdown and checks that every image a page references exists, and
`.github/workflows/site.yml` renders the site and checks its local links and anchors with
`scripts/check_site.py`.
