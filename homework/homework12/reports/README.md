# Stage 12 Reports

## Audience
The primary audience is a **portfolio / risk manager** who needs a concise decision summary rather than implementation-level detail.

## Why this format fits
The stakeholder deliverable is a short Markdown report because it is easy to review in GitHub, keeps charts and assumptions adjacent to the decisions they support, and can be exported to PDF later if needed.

The executed Jupyter notebook serves as a **second, analyst-facing format**. It contains the reproducible calculations, sensitivity table construction, chart-generation code, assumptions, and technical notes. This separation lets decision-makers receive concise conclusions while analysts can audit the workflow.

## Files
- `final_report.md` — stakeholder-facing final report
- `images/risk_return_by_scenario.png` — risk–return scatter
- `images/return_sensitivity_vs_baseline.png` — quantified scenario sensitivity
- `images/illustrative_value_path.png` — illustrative economic magnitude
- `../data/processed/final_results.csv` — scenario-level source data
- `../data/processed/sensitivity_summary.csv` — quantified sensitivity table

## Reproducibility
Run `homework12_results-reporting-delivery-design_submission.ipynb` from top to bottom. It recreates the fallback data when needed and regenerates every report figure and table.
