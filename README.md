# DD104 — Pre-Silicon Verification

Verilator and cocotb: find the bugs hiding in a real 8-bit core.

Part of the UofT ASIC Team education materials (`uoftasic`).
Course site: <https://uoftasic.com/dd104/> · Education hub: <https://edu.uoftasic.com/>

SimProc, an 8-bit processor, ships with one test, and that test passes on thirteen deliberately
broken versions of the chip. This course is about the gap between "my tests pass" and "this design
works".

## Quick start

Everything runs inside the team workbench image `hpretl/iic-osic-tools:2026.08` (cocotb 2.0.1,
Icarus Verilog 14.0, Verilator 5.050). Every lab package runs with `make` alone, in a bare
container, with no environment setup, and every one prints a verdict.

Students set up through the shared `workspace` and the noVNC desktop from
[IC101](https://uoftasic.com/ic101/); [Lab 01, Part 1](https://uoftasic.com/dd104/labs/lab-01-the-adder-you-already-trust-overview.html)
has the steps. In a terminal on that desktop:

```bash
. /foss/designs/common/.designinit
mod add dd104                                       # first time only
mod dd104
cd labs/lab-01-the-adder-you-already-trust && make  # ends on VERDICT: FAIL, on purpose
```

Without the desktop, from a clone of this repo:

```bash
git clone https://github.com/uoftasic/dd104.git
cd dd104
docker run --rm --user "$(id -u):$(id -g)" -v "$PWD:/work" -w /work \
  hpretl/iic-osic-tools:2026.08 --skip bash -c \
  'cd /work/labs/lab-01-the-adder-you-already-trust && make'
```

## Lab packages

| Path | What it is | Writeup |
|---|---|---|
| `labs/lab-01-the-adder-you-already-trust/` | a testbench that cannot tell a good adder from a broken one | Lab 01 |
| `labs/cocotb-intro/` | cocotb on an 8-bit counter: triggers, the 1.x traps, a two-sided verdict, waveforms | cocotb on a counter |
| `labs/lab-02-the-only-test-this-chip-has/` | `make shuttle`: 13 of 13 broken cores pass the shipped test | Lab 02 |
| `labs/lab-03-three-blocks-before-the-processor/` | unit tests for `program_counter`, `register_file` and `ALU` | Lab 03 |
| `labs/lab-04-your-first-bug-hunt/` | `make new` deals a mystery core; `make verdict` grades you | Lab 04 |
| `labs/lab-05-every-answer-is-right/` | two bugs invisible to architectural state | Lab 05 |
| `labs/lab-06-capstone/` | one suite that catches all thirteen, plus a bug report | Lab 06 |
| `labs/common/` | the shared harness, golden model, bug catalogue and verdict machinery | used by Labs 02–06 |
| `labs/simproc/` | the forked SimProc RTL, the thirteen bug variants, and their verification | instructor side |

Reference solutions live in each package's `solutions/`. `labs/common/bugs.py` is the answer key;
reading it is the one thing that can make this course worthless to a student.

## Docs

The course site is built with Quarto from `./docs`. `docs/_quarto.yml` holds the site, sidebar
and navbar, and `docs/_quarto-pdf.yml` builds the whole course as one PDF. To preview it you need
[Quarto](https://quarto.org/docs/get-started/) 1.11:

```bash
quarto preview docs                            # -> http://localhost:4200
quarto render docs --profile pdf --to typst    # whole course as one PDF in docs/_book/
```

| Path | On Pages? | Purpose |
|------|-----------|---------|
| `docs/` | Yes | The course site; `docs/index.md` is the home page and has the Course path |
| `docs/guide/` | Yes | Guide pages: reading only, no commands |
| `docs/labs/` | Yes | Lab writeups: every command a student runs, in numbered parts and steps |
| `docs/reference/` | Yes | Lookup pages: instruction set, harness API, output that is not an error |
| `labs/` | No | Runnable packages |
| `scripts/` | No | `check_site.py`, the link check for the rendered site; the rest is template scaffolding |
| `notebooks/`, `data/`, `figures/` | No | Repo scaffolding, unused by DD104 |

GitHub Pages is set to Source: GitHub Actions. On every push to `main` that touches `docs/`,
`scripts/check_site.py` or the workflow itself, `.github/workflows/site.yml` renders the site (with a PDF of every page) and the course PDF,
checks the rendered site's local links and anchors with `scripts/check_site.py`, and deploys
`docs/_site`.

This repo was created from [uoftasic/course-template](https://github.com/uoftasic/course-template).
`TEMPLATE.md` and `scripts/init-template.py` are that template's bootstrap files and are not part
of the course. `ORI-DECISION.md` records why the course specifies `ORI` as writing `r0`.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE) — Copyright UofT ASIC Team / `uoftasic`.
`labs/simproc/` is a fork; see `labs/simproc/FORKED-FROM` and `labs/simproc/LICENSE.upstream`.
