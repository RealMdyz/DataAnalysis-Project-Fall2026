# Data Analysis Course Project — Fall 1405 (2026)

**Track:** B — Amazon Reviews'23 (text + structured data, multimodal)
**Title (working):** Review-driven product improvement priorities
**Author:** Mohammad Yasin Zare

From the reviews a product received in a time window (default: last 3 months),
estimate which product aspects pulled customer satisfaction down the most, and
rank them as improvement priorities for the product owner.

## How to reproduce
1. Create an environment and run `pip install -r requirements.txt`
2. Download the raw files: `python src/download_data.py`
   (resumes interrupted downloads; writes sizes and SHA-256 to `data/download_manifest.json`)
3. Optional: `python src/scan_category.py` re-counts the candidate subsets
   (`reports/phase1/category_scan.json`)
4. Build the subset: `python src/build_subset.py`
   (writes `data/processed/meta_rc.parquet` and `reviews_rc.parquet`)
5. Run the notebooks in `notebooks/` in numeric order (01 to 08)

All settings (category, subset rule, window, split dates, metrics, seed = 42)
live in `configs/config.yaml`. Raw and processed data are not committed.

## Phase 1 at a glance
- Report: [`reports/phase1.pdf`](reports/phase1.pdf) (Persian); every number is traced
  to its source in [`reports/phase1/numbers_sheet.md`](reports/phase1/numbers_sheet.md)
- Subset: 71,046 remote-controlled products, 862,444 reviews
  (777,860 in the analysis period, Jan 2015 to Mar 2023)
- Report unit: product x 3-month window with >= 20 reviews (5,070 units)
- Split: temporal; train 2015-2020, validation 2021, test 2022 to Mar 2023 (locked)
- Primary metric: macro-MAE; text baseline (TF-IDF + Ridge) = 0.724 on validation


## 🔍 Phase 2 Highlights: Aspect Discovery & Feature Engineering
- **Aspect Discovery (k=5):** Unsupervised K-Means clustering on UMAP-reduced sentence embeddings (derived from 139,520 extracted sentences in the training period 2015–2020). Identified 5 core product aspects: RC Car Performance, Buying Value & Price, Drone Flight & Camera, Battery & Charging, and Gift & Kids Engagement.
- **Pattern Stability:** Verified cluster robustness using Adjusted Rand Index (ARI), achieving high stability across random seeds ($\text{ARI} = 0.9682$) and 80% subsamples ($\text{ARI} = 0.9710$).
- **Multimodal Feature Matrix:** Generated a review-level engineered dataset containing 30 features (`14,792 × 30`) stored at `data/processed/phase2_train_engineered_features.parquet`.
- **Phase Report:** The comprehensive Phase 2 report (including UMAP visualizations, Silhouette/Elbow analysis, and the 30-feature catalog) is available as both Markdown (`reports/phase2/phase2.md`) and a formatted PDF (`reports/phase2/phase2.pdf`).

## 🛠️ Reproducing the Phase 2 Report
To automatically build or update the Phase 2 report PDF from the Markdown source and embedded figures, run the provided build script:
```bash
python src/build_phase2_report.py

| Notebook | Content |
|---|---|
| `01_structure_audit` | Files, columns, identifiers, joins, time range |
| `02_data_quality` | Missing values, duplicates, impossible values, outliers |
| `03_multimodal_audit` | Availability of each modality; is missingness random? |
| `04_text_audit` | Length, short/long reviews, language, text vs rating |
| `05_eda` | Univariate and multivariate EDA |
| `06_window_feasibility` | Report units, minimum reviews, analysis period, consecutive pairs |
| `07_leakage_split` | Leakage risks and the temporal split |
| `08_baselines` | Target, metrics and six baselines |
| `09_phase2_preprocessing` | Sentence extraction, dual text representation (TF-IDF & Sentence Transformers), and UMAP |
| `10_phase2_clustering` | K-Means aspect discovery ($k=5$), elbow/silhouette selection, and interpretation |
| `11_phase2_stability_and_features` | Cluster stability evaluation (ARI) and review-level multimodal feature engineering (30 features) |

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
| 1 — Problem, data audit, EDA | 12 Aban 1405 | `phase-1` | done |
| 2 — Preprocessing, features, pattern discovery | 27 Aban 1405 | `phase-2` | done |
| 3 — Predictive modeling & experiment design | 27 Azar 1405 | `phase-3` | — |
| 4 — Interpretation, subgroups, decisions | 15 Dey 1405 | `phase-4` | — |
| 5 — Robustness & final report | 5 Bahman 1405 | `phase-5-final` | — |
