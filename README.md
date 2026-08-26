# DD104 — Pre-Silicon Verification

Verilator and cocotb: find the bugs hiding in a real 8-bit core.

Part of the **UofT ASIC Team** education materials (`uoftasic`).
Course site: **https://uoftasic.com/dd104/** · Education hub: https://edu.uoftasic.com/

An 8-bit processor, SimProc, ships with one test. That test passes on thirteen deliberately
broken versions of the chip. This course is about the gap between "my tests pass" and "this
design works".

## Quick start

Everything runs inside the team workbench image `hpretl/iic-osic-tools:2026.04`
(cocotb 2.0.1, Icarus Verilog 14.0, Verilator 5.046). **Every lab package runs with `make`
alone, in a bare container, with no environment setup**, and every one prints a verdict.

```bash
git clone https://github.com/uoftasic/dd104.git
cd dd104/labs/lab-01-the-adder-you-already-trust
make                     # ends on VERDICT: FAIL, on purpose
```

Outside the noVNC desktop, the same thing directly:

```bash
docker run --rm --user "$(id -u):$(id -g)" -v "$PWD:/work" -w /work \
  hpretl/iic-osic-tools:2026.04 --skip bash -c \
  'cd /work/labs/lab-01-the-adder-you-already-trust && make'
```

Setup, versions and the noVNC desktop: [Getting started](https://uoftasic.com/dd104/#/guide/getting-started).

## Lab packages

| Path | What it is |
|---|---|
| `labs/cocotb-intro/` | cocotb on an 8-bit counter — `make`, `make oldapi`, `make nothing` |
| `labs/lab-01-the-adder-you-already-trust/` | a testbench that cannot tell a good adder from a broken one |
| `labs/lab-02-the-only-test-this-chip-has/` | `make shuttle` — 13 of 13 broken cores pass the shipped test |
| `labs/lab-03-three-blocks-before-the-processor/` | unit-testing `program_counter`, `register_file`, `ALU` |
| `labs/lab-04-your-first-bug-hunt/` | `make new` deals a mystery core; `make verdict` grades you |
| `labs/lab-05-every-answer-is-right/` | two bugs invisible to architectural state |
| `labs/lab-06-capstone/` | one suite that catches all thirteen, plus a bug report |
| `labs/common/` | the shared harness, golden model, bug catalogue and verdict machinery |
| `labs/simproc/` | the forked SimProc RTL, the thirteen bug variants, and their verification |

Reference solutions live in each package's `solutions/`. `labs/common/bugs.py` is the answer
key — reading it is the one thing that can make this course worthless to you.

## Docs

The course site is plain Docsify from `./docs`, no build step:

```bash
npx docsify-cli serve docs      # → http://localhost:3000
```

| Path | On Pages? | Purpose |
|------|-----------|---------|
| `docs/` | **Yes** | The course site |
| `docs/labs/` | Yes | Lab writeups (theory, procedure, expected results) |
| `labs/` | No | Runnable packages |
| `scripts/`, `notebooks/`, `data/`, `figures/` | No | Repo scaffolding, unused by DD104 |

GitHub Pages: deploy from a branch, `main`, folder `/docs`. No Actions deploy step needed.

This repo was created from [uoftasic/course-template](https://github.com/uoftasic/course-template);
`TEMPLATE.md` and `scripts/init-template.py` are that template's own bootstrap files and are
not part of the course.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE) — Copyright UofT ASIC Team / `uoftasic`.
`labs/simproc/` is a fork; see `labs/simproc/FORKED-FROM` and `labs/simproc/LICENSE.upstream`.
