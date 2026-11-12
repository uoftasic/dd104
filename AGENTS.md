# Agent guide — UofT ASIC course repos

You are working in a course repository for the UofT ASIC Team (`uoftasic`): teaching materials for IC, RTL, FPGA and open-source ASIC flows. The site under `docs/` is published on GitHub Pages (Docsify, no build step). Runnable work lives outside `docs/`.

Optimise for a clear student path through the course, not for template maintenance. Prefer concrete labs and notes students can follow end to end over meta documentation.

## Goals

- Teach IC development skills: RTL (SystemVerilog/Verilog), simulation, synthesis, FPGA bring-up, and/or open ASIC flows (e.g. Yosys, LibreLane, SKY130) as the course requires.
- Keep the Course path table in `docs/README.md` current: numbered rows that alternate Read (guide pages) and Do (one lab), each with a time estimate, under the columns `| # | | What | Time |`. Read and Do are plain text. A Do row links the lab as `Lab NN: Title` and ends with one sentence on what the student will do. The row times add up to the total time stated on the home page. `docs/_sidebar.md` follows the same order and uses the same `Lab NN: Title` names.
- Guide pages are reading only. Lab writeups are the only place a student is told to run something.
- Separate what students read (`docs/`) from what they run (`labs/`, `scripts/`, `notebooks/`).
- Never publish grades, solution keys, or PII under `docs/`. Put keys in `labs/**/solutions/` and gitignore them on student forks when policy requires.

## Layout (do not fight this)

| Path | Published? | Put here |
|------|------------|----------|
| `docs/` | Yes | Guides, lab writeups, figures for the site |
| `docs/guide/` | Yes | Conceptual notes (flows, tools, theory); no required commands |
| `docs/labs/` | Yes | Lab writeups only (`<lab-id>-overview.md`); every command lives here |
| `docs/reference/` | Yes | Lookup pages: tables and short entries |
| `docs/assets/img/` | Yes | Small diagrams / waveforms for docs |
| `labs/<lab-id>/` | No | HDL, Python, testbenches, local data, graders |
| `scripts/` | No | Course utilities / automation |
| `notebooks/` | No | Exploratory or assignment notebooks |
| `data/`, `figures/` | No | Shared datasets / source figures |

Site wiring: `docs/index.html`, `docs/_sidebar.md`, `docs/_navbar.md`. Math: `$inline$`, `$$display$$`.

## Adding a lab (preferred unit of coursework)

Lab IDs: `lab-NN-short-name` (e.g. `lab-02-counter-sv`).

1. Create `labs/<lab-id>/` with at least:
   - `README.md` — points at the Docsify writeup and how to run
   - `src/` — HDL / Python / entrypoints
   - `data/` — small inputs (large binaries → Git LFS or external)
   - `requirements.txt` or tool notes when needed
2. Add `docs/labs/<lab-id>-overview.md`, titled `# Lab NN: Title`, with: what you'll build or measure (2–3 lines); a time estimate; Before you start (guide pages to read first, setup); numbered parts, each opening with the one question it answers and made of numbered steps ending in a concrete "Check:"; and Finishing. At least one required part has the student produce something (edit a file, write a test, or work out a number before checking it). Questions students must answer go at the step where they arise, with the answer in a collapsed `<details><summary>Answer</summary>` block under the question; ask for a prediction before a run wherever the student can make one. Optional parts go at the end, marked "(optional)" in the header and left out of the time estimate.
   Finishing has three things, in this order: "You're done when" (one checkable line tied to the student's own work, not to the shipped package passing); "Questions", if any, each with a collapsed answer or a pointer to the step that answers it; and "Submit" (what to submit, or nothing). After Finishing come "Going further (optional)", if any, and a last line, "Next on the Course path: …".
3. Add a Do row to the Course path in `docs/README.md` (link text `Lab NN: Title`, then one sentence on what the student will do, and update the total time) and link the writeup from `docs/_sidebar.md` in the same position (and `_navbar.md` only if it belongs in top nav).
4. Cross-link: writeup → GitHub `labs/<lab-id>/`; package README → `docs/labs/<lab-id>-overview.md`.

Guide pages teach, writeups direct the doing, and packages execute. Do not paste long HDL into Docsify pages; link to the files under `labs/`. A package README is short: a link to the writeup, how to run, the make targets and the file list.

## Adding a guide page

1. Add kebab-case Markdown under `docs/guide/` (e.g. `yosys-synth.md`). Keep it to reading: if the page needs the student to run something, put that step in the matching lab writeup and leave a one-line pointer.
2. Add it to a Read row of the Course path and link it from `docs/_sidebar.md` in the same order.
3. Images under `docs/assets/img/` with paths relative to `docs/`.
4. Prefer relative Docsify links between pages; use GitHub URLs for `labs/` and `scripts/`.

## Pedagogy checklist (use when authoring)

- State learning objectives in student language (“You will synthesize a counter and inspect the netlist”).
- Assume a clone of this repo and the course’s documented workbench; do not bundle Docker in every lab unless the course already does.
- For EDA-heavy work (LibreLane / SKY130 / IIC-OSIC-TOOLS), document the team workbench steps in the course rather than inventing a one-off container story.
- Keep procedures copy-pasteable (`cd`, install, simulate/synth, check artifact).
- Define expected results (printout, waveform check, area/timing ballpark, golden hash) so students know they succeeded.
- Progress difficulty across labs; reuse naming and directory conventions so later labs feel familiar.
- Prefer small, inspectable designs over opaque blobs; when using IP or PDK artifacts, keep secrets and huge binaries out of git.

## Tooling norms

- Python helpers and graders: under `labs/<id>/src/` or `scripts/`; list entry points in the nearest `README.md`.
- SystemVerilog/Verilog: under `labs/<id>/src/` (or `rtl/`, `tb/` if you split — stay consistent within the course).
- Heavy outputs (GDS, large FSDB/VCD, PDK caches): local `results/` or LFS — never under `docs/`.
- Preview docs locally: `npx docsify-cli serve docs` → http://localhost:3000

## What not to do

- Do not add maintainer-only pages to the published site (contributing guides, template notes, notation stubs “for debugging”).
- Do not put solution keys or rubrics in `docs/`.
- Do not replace student-facing content with template/bootstrap instructions; point humans at `CONTRIBUTING.md` / `TEMPLATE.md` only when they are bootstrapping or changing repo conventions.
- Do not change org assumptions: GitHub org is `uoftasic`; course id matches the repo name.

## Quick references

- Repo conventions: `CONTRIBUTING.md`
- Bootstrap tokens / Pages checklist: `TEMPLATE.md`
- Sample lab shape: `labs/lab-01-the-adder-you-already-trust/` + `docs/labs/lab-01-the-adder-you-already-trust-overview.md`
