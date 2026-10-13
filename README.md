# Data Analysis Course Project — Fall 1405 (2026)

**Track:** B — Amazon Reviews'23 (text + structured data, multimodal)
**Title (working):** Review-driven product improvement priorities
**Author:** Mohammad Yasin Zare

From the reviews a product received in a time window (default: last 3 months),
estimate which product aspects pulled customer satisfaction down the most, and
rank them as improvement priorities for the product owner.

## How to reproduce
1. Create an environment and run `pip install -r requirements.txt`
2. Download the raw files listed in `data/README.md` into `data/raw/`
3. Check settings (category, window length, seed) in `configs/config.yaml`
4. Run the notebooks in `notebooks/` in numeric order

## Repository layout
| Path | Content |
|---|---|
| `PROJECT_CARD.md` | Problem framing (14 required items) |
| `AI_USAGE.md` | Log of AI/LLM tool usage (required) |
| `configs/` | Project settings: category, window length, seeds |
| `data/README.md` | Data source, files, download date, subset rules |
| `src/` | Reusable Python code (loading, auditing, features) |
| `notebooks/` | Analysis notebooks, one per step |
| `figures/` | Final figures used in reports |
| `models/` | Saved models (large files are not committed) |
| `reports/phaseN/` | Phase reports (PDF) |

## Phase status
| Phase | Deadline | Tag | Status |
|---|---|---|---|
| 1 — Problem, data audit, EDA | 12 Aban 1405 | `phase-1` | in progress |
| 2 — Preprocessing, features, pattern discovery | 27 Aban 1405 | `phase-2` | — |
| 3 — Predictive modeling & experiment design | 27 Azar 1405 | `phase-3` | — |
| 4 — Interpretation, subgroups, decisions | 15 Dey 1405 | `phase-4` | — |
| 5 — Robustness & final report | 5 Bahman 1405 | `phase-5-final` | — |
