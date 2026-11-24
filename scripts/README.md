# Scripts

Utilities for DD104 — Pre-Silicon Verification under the UofT ASIC org (`uoftasic`).

## Entry points

| Script | Purpose |
|--------|---------|
| `check_site.py` | Check every local link and `#anchor` in the rendered Quarto site, and that every page has the navbar's link to https://edu.uoftasic.com/; `.github/workflows/site.yml` runs it as `python3 scripts/check_site.py docs/_site` |
| `hello.py` | Smoke-check that Python runs in this clone |
| `init-template.py` | Fill `dd104` / title / description after using the template |
| `figures/` | The scripts that draw the diagrams in `docs/assets/img/` with schemdraw. `pip install -r scripts/figures/requirements.txt`, then `python3 scripts/figures/<name>.py` rewrites that figure's SVG |

## Usage

```bash
# From repo root
python3 scripts/hello.py

python3 scripts/init-template.py \
  --id dd103 \
  --title "DD103 — RTL on FPGAs & ASICs" \
  --description "RTL on FPGAs and open-source ASIC flows"
```

## Conventions

- Prefer Python; HDL tooling belongs in `labs/` or the shared workbench.
- No secrets in the repo; use `.env.example` if configuration is needed.
- Document new scripts here when you add them.
