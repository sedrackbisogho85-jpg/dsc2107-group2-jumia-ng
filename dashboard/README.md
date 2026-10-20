# Jumia Nigeria Seven-Day Product Analysis Dashboard

## What the Dashboard Shows
This interactive Streamlit dashboard visualizes the completed seven-day Jumia Nigeria product analysis for **Phones & Tablets, Computing, and Electronics** (13–19 October 2026). It provides:

- **Overview**: Key metrics (filtered observations, unique products, median USD price, % discounted) and breakdowns by date and category.
- **Price & Discount Analysis**: Boxplots, distributions, trends, and comparison of displayed vs calculated discounts.
- **Ratings & Popularity**: Relationships between price/rating and review count/rating, median ratings by category, and top-reviewed products.
- **Seven-Day Movement**: Price movement analysis (increases/decreases/unchanged), largest changes, daily medians, discount movement, and product visibility.
- **Brands & Product Table**: Brand rankings and a searchable, filterable product table with CSV download.
- **Kenya vs Nigeria (Optional)**: Only shown if comparison files are present locally.

## Data File Used
The dashboard loads the final combined cleaned CSV:
```
data/cleaned/jumia_ng_products_2026-10-13_to_2026-10-19_cleaned.csv
```

This file uses relative paths, so the dashboard works if the repository is moved to another computer. All monetary values displayed are in USD.

## Installation

Install required packages:
```bash
pip install -r requirements.txt
```

The required packages for the dashboard are `streamlit` and `plotly`. If they are already present in `requirements.txt`, no changes are made.

## How to Launch
From the repository root:
```bash
python -m streamlit run dashboard/app.py
```

The app will open in your default browser. No authentication or external services are required.

## How the Filters Work
The sidebar provides the following filters (all work together and update results dynamically):
1. **Collection Date** – Select one or more scrape dates.
2. **Category** – Filter by Phones & Tablets, Computing, or Electronics.
3. **Brand** – Filter by brand (all by default).
4. **USD Price Range** – Minimum and maximum current price.
5. **Discounted/Not Discounted** – All, only discounted, or only non-discounted.
6. **Minimum Rating** – Filter by minimum rating value.
7. **Reset Filters** – Restore default selections.

## Main Limitations
- Results describe observed catalogue listings, **not completed sales**. Review counts do not equal sales.
- Correlation does not imply causation (price vs rating weak positive; review count vs rating weak negative).
- Missing values (old prices: 199; ratings: 25 in the full dataset) are preserved and do not crash the app.
- Outliers are not removed; logarithmic axis option is provided for price visualizations.
- Kenya/Nigeria comparison is optional and only included if source files exist locally.
- If recalculated movement statistics differ from historical reference values, the dashboard reports calculated values from the filtered/unfiltered data as appropriate.

## Notes
This is a descriptive, student-level dashboard appropriate for Year 2 Semester 1 Data Mining and Wrangling. No advanced ML, no modifications to raw/accepted deliverables, and no Git operations are performed.
