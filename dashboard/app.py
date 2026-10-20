import os
from pathlib import Path
from typing import Optional, List

import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard_utils import load_data, find_dataset_path


st.set_page_config(
    page_title="Jumia Nigeria Seven-Day Product Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Jumia Nigeria Seven-Day Product Analysis")
st.subheader("Phones & Tablets, Computing and Electronics — 13–19 October 2026")
st.markdown("**DSC2107 Data Mining and Wrangling — Group 2**")


@st.cache_data(ttl=3600, show_spinner=False)
def get_data():
    return load_data()


def format_usd(val: Optional[float]) -> str:
    if val is None or pd.isna(val):
        return "—"
    try:
        return f"${val:,.2f}"
    except Exception:
        return f"${val}"


def main():
    try:
        df, warnings_list = get_data()
    except Exception as e:
        st.error(f"Failed to load data: {e}")
        return

    if warnings_list:
        for w in warnings_list:
            st.warning(w)

    with st.sidebar:
        st.header("Filters")

        # Date selection
        if 'scrape_date' in df.columns:
            dates = sorted(df['scrape_date'].dropna().unique().tolist())
        else:
            dates = []
        if dates:
            date_sel = st.multiselect("Collection Date", dates, default=dates)
        else:
            date_sel = []

        # Category
        cats = sorted(df['category'].dropna().unique().tolist()) if 'category' in df.columns else []
        if cats:
            cat_sel = st.multiselect("Category", cats, default=cats)
        else:
            cat_sel = []

        # Brand
        brands = sorted(df['brand_clean'].dropna().unique().tolist()) if 'brand_clean' in df.columns else []
        brand_sel = st.multiselect("Brand", brands, default=None, placeholder="All brands")

        # Price range
        price_col = df['current_price_num'] if 'current_price_num' in df.columns else None
        if price_col is not None:
            pmin = float(price_col.min()) if price_col.notna().any() else 0.0
            pmax = float(price_col.max()) if price_col.notna().any() else 0.0
            if pmax < pmin:
                pmin, pmax = pmax, pmin
            price_range = st.slider("USD Price Range", min_value=pmin, max_value=pmax, value=(pmin, pmax), step=0.01)
        else:
            price_range = (0, 0)

        # Discounted
        disc_opts = ['All', 'Discounted', 'Not Discounted']
        disc_sel = st.selectbox("Discount Status", disc_opts, index=0)

        # Rating
        rating_col = df['rating_num'] if 'rating_num' in df.columns else None
        if rating_col is not None and rating_col.notna().any():
            rmin_data = float(rating_col.min())
            rmax_data = float(rating_col.max())
            rmin = st.number_input("Minimum Rating", min_value=rmin_data, max_value=rmax_data, value=rmin_data, step=0.1)
        else:
            rmin = 0.0

        if st.button("Reset Filters"):
            st.rerun()

    # Apply filters
    dff = df.copy()
    if date_sel:
        dff = dff[dff['scrape_date'].isin(date_sel)]
    if cat_sel:
        dff = dff[dff['category'].isin(cat_sel)]
    if brand_sel:
        dff = dff[dff['brand_clean'].isin(brand_sel)]
    if price_col is not None and 'price_range' in locals():
        pmin_r, pmax_r = price_range
        dff = dff[dff['current_price_num'].between(pmin_r, pmax_r, inclusive='both') | dff['current_price_num'].isna()]

    if disc_sel == 'Discounted':
        dff = dff[dff['is_discounted'] == True]
    elif disc_sel == 'Not Discounted':
        dff = dff[dff['is_discounted'] == False]

    if rating_col is not None:
        dff = dff[(dff['rating_num'] >= rmin) | dff['rating_num'].isna()]

    tabs = st.tabs([
        "Overview",
        "Price & Discount Analysis",
        "Ratings & Popularity",
        "Seven-Day Movement",
        "Brands & Product Table",
        "Kenya vs Nigeria (Optional)",
    ])

    with tabs[0]:
        st.subheader("Overview")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Filtered Observations", f"{len(dff):,}")
        c2.metric("Unique Products", f"{dff['source_product_id'].nunique() if 'source_product_id' in dff else 0:,}")
        med_price = dff['current_price_num'].median() if 'current_price_num' in dff else None
        c3.metric("Median Price (USD)", format_usd(med_price))
        if len(dff) > 0:
            pct_disc = (dff['is_discounted'].sum() / len(dff)) * 100.0
        else:
            pct_disc = 0.0
        c4.metric("Discounted Products (%)", f"{pct_disc:.1f}%")

        col_a, col_b = st.columns(2)
        with col_a:
            if 'scrape_date' in dff.columns:
                obs_by_day = dff.groupby('scrape_date', dropna=True).size().reset_index(name='observations')
                if not obs_by_day.empty:
                    fig = px.bar(obs_by_day, x='scrape_date', y='observations', title='Observations Collected Per Day',
                                 labels={'scrape_date': 'Collection Date', 'observations': 'Observations'})
                    st.plotly_chart(fig, use_container_width=True)
        with col_b:
            if 'category' in dff.columns:
                uniq_by_cat = dff.groupby('category', dropna=True)['source_product_id'].nunique().reset_index(name='unique_products')
                if not uniq_by_cat.empty:
                    fig = px.bar(uniq_by_cat, x='category', y='unique_products', title='Unique Products by Category',
                                 labels={'category': 'Category', 'unique_products': 'Unique Products'})
                    st.plotly_chart(fig, use_container_width=True)

        col_c, col_d = st.columns(2)
        with col_c:
            if 'category' in dff.columns and 'current_price_num' in dff.columns:
                med_by_cat = dff.groupby('category', dropna=True)['current_price_num'].median().reset_index(name='median_price_usd')
                if not med_by_cat.empty:
                    fig = px.bar(med_by_cat, x='category', y='median_price_usd', title='Median USD Price by Category',
                                 labels={'category': 'Category', 'median_price_usd': 'Median Price (USD)'})
                    st.plotly_chart(fig, use_container_width=True)
        with col_d:
            if 'category' in dff.columns:
                g = dff.groupby('category', dropna=True)
                disc_share = (g['is_discounted'].sum() / g.size() * 100.0).reset_index(name='discount_share_pct')
                if not disc_share.empty:
                    fig = px.bar(disc_share, x='category', y='discount_share_pct', title='Discounted-Product Share by Category',
                                 labels={'category': 'Category', 'discount_share_pct': '% Discounted'})
                    st.plotly_chart(fig, use_container_width=True)

    with tabs[1]:
        st.subheader("Price & Discount Analysis")
        use_log = st.checkbox("Use logarithmic price axis (recommended due to outliers)")

        if 'category' in dff.columns and 'current_price_num' in dff.columns:
            fig = px.box(dff.dropna(subset=['current_price_num']), x='category', y='current_price_num',
                         title='USD Price by Category', log_y=use_log,
                         labels={'category': 'Category', 'current_price_num': 'Price (USD)'})
            st.plotly_chart(fig, use_container_width=True)

        if 'current_price_num' in dff.columns:
            fig = px.histogram(dff.dropna(subset=['current_price_num']), x='current_price_num',
                               title='Price Distribution', log_x=use_log, nbins=40,
                               labels={'current_price_num': 'Price (USD)'})
            st.plotly_chart(fig, use_container_width=True)

        if 'discount_pct_num' in dff.columns:
            fig = px.histogram(dff.dropna(subset=['discount_pct_num']), x='discount_pct_num',
                               title='Discount Percentage Distribution', nbins=30,
                               labels={'discount_pct_num': 'Discount %'})
            st.plotly_chart(fig, use_container_width=True)

        if 'scrape_date' in dff.columns and 'category' in dff.columns and 'current_price_num' in dff.columns:
            med_trend = dff.groupby(['scrape_date', 'category'], dropna=True)['current_price_num'].median().reset_index(name='median_price_usd')
            if not med_trend.empty:
                fig = px.line(med_trend, x='scrape_date', y='median_price_usd', color='category',
                              title='Median Price Trend by Date and Category',
                              labels={'scrape_date': 'Date', 'median_price_usd': 'Median Price (USD)', 'category': 'Category'})
                st.plotly_chart(fig, use_container_width=True)

        # Displayed vs calculated discount
        if 'displayed_discount_percentage_num' in dff.columns and 'calculated_discount_percentage_num' in dff.columns:
            comp = dff[['displayed_discount_percentage_num', 'calculated_discount_percentage_num']].dropna(how='all')
            if not comp.empty:
                st.subheader("Displayed Discount vs Calculated Discount")
                st.dataframe(comp.sample(n=min(100, len(comp))).rename(columns={
                    'displayed_discount_percentage_num': 'Displayed Discount %',
                    'calculated_discount_percentage_num': 'Calculated Discount %',
                }))

    with tabs[2]:
        st.subheader("Ratings & Popularity")
        col_p, col_r = st.columns(2)
        with col_p:
            if 'current_price_num' in dff.columns and 'rating_num' in dff.columns:
                sample = dff.dropna(subset=['current_price_num', 'rating_num'])
                if len(sample) > 5000:
                    sample = sample.sample(5000)
                fig = px.scatter(sample, x='current_price_num', y='rating_num', opacity=0.6,
                                 title='Price vs Rating',
                                 labels={'current_price_num': 'Price (USD)', 'rating_num': 'Rating'})
                st.plotly_chart(fig, use_container_width=True)

        with col_r:
            if 'review_count_num' in dff.columns and 'rating_num' in dff.columns:
                sample = dff.dropna(subset=['review_count_num', 'rating_num'])
                if len(sample) > 5000:
                    sample = sample.sample(5000)
                fig = px.scatter(sample, x='review_count_num', y='rating_num', opacity=0.6,
                                 title='Review Count vs Rating',
                                 labels={'review_count_num': 'Review Count', 'rating_num': 'Rating'})
                st.plotly_chart(fig, use_container_width=True)

        if 'category' in dff.columns and 'rating_num' in dff.columns:
            med_r = dff.groupby('category', dropna=True)['rating_num'].median().reset_index(name='median_rating')
            fig = px.bar(med_r, x='category', y='median_rating', title='Median Rating by Category',
                         labels={'category': 'Category', 'median_rating': 'Median Rating'})
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("Most-Reviewed Products")
        if 'source_product_id' in dff.columns:
            top = dff.sort_values('review_count_num', ascending=False, na_position='last').drop_duplicates('source_product_id').head(20)
            cols = ['product_name', 'brand_clean', 'category', 'current_price_num', 'rating_num', 'review_count_num', 'product_url']
            show = top[[c for c in cols if c in top.columns]].copy()
            if 'current_price_num' in show:
                show['Price (USD)'] = show['current_price_num'].apply(format_usd)
                show = show.drop(columns=['current_price_num'])
            if 'rating_num' in show:
                show['Rating'] = show['rating_num'].apply(lambda x: f"{x:.1f}" if pd.notna(x) else '—')
                show = show.drop(columns=['rating_num'])
            if 'review_count_num' in show:
                show['Review Count'] = show['review_count_num'].apply(lambda x: f"{int(x):,}" if pd.notna(x) else '—')
                show = show.drop(columns=['review_count_num'])
            show = show.rename(columns={'product_name': 'Product', 'brand_clean': 'Brand', 'category': 'Category', 'product_url': 'URL'})
            st.dataframe(show, use_container_width=True, hide_index=True)

        st.info(
            "Interpretation: Price and rating had a very weak positive relationship; review count and rating had a weak negative relationship. "
            "Correlation does not prove causation. Review counts do not equal sales."
        )
        st.caption("Full unfiltered reference: price vs rating Spearman ρ ≈ 0.110; review count vs rating Spearman ρ ≈ -0.215 (for reference only).")

    with tabs[3]:
        st.subheader("Seven-Day Movement")
        if 'source_product_id' in dff.columns and 'scrape_date' in dff.columns and 'current_price_num' in dff.columns:
            prod_dates = dff[['source_product_id', 'scrape_date', 'scrape_date_dt', 'current_price_num']].dropna(subset=['current_price_num', 'scrape_date'])
            if not prod_dates.empty:
                prod_dates = prod_dates.sort_values(['source_product_id', 'scrape_date_dt'])

                # First and last
                first = prod_dates.groupby('source_product_id').first().reset_index()
                last = prod_dates.groupby('source_product_id').last().reset_index()
                fl = first[['source_product_id', 'current_price_num']].merge(
                    last[['source_product_id', 'current_price_num']], on='source_product_id', suffixes=('_first', '_last')
                )
                fl = fl.dropna(subset=['current_price_num_first', 'current_price_num_last'])

                increased = len(fl[fl['current_price_num_last'] > fl['current_price_num_first']])
                decreased = len(fl[fl['current_price_num_last'] < fl['current_price_num_first']])
                unchanged = len(fl[fl['current_price_num_last'] == fl['current_price_num_first']])
                comparable = len(fl)

                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Comparable Products (first-last)", f"{comparable:,}")
                c2.metric("Increased", f"{increased:,}")
                c3.metric("Decreased", f"{decreased:,}")
                c4.metric("Unchanged", f"{unchanged:,}")

                # Changed at least once
                changes = prod_dates.groupby('source_product_id')['current_price_num'].nunique()
                changed_once = (changes > 1).sum()
                st.metric("Products Changed Price At Least Once", f"{changed_once:,}")

                # Price change events
                price_changes_events = 0
                try:
                    g = prod_dates.groupby('source_product_id')
                    for pid, grp in g:
                        prices = grp['current_price_num'].tolist()
                        for p1, p2 in zip(prices[:-1], prices[1:]):
                            if p1 != p2:
                                price_changes_events += 1
                except Exception:
                    price_changes_events = 0
                st.metric("Price Changes Recorded", f"{price_changes_events:,}")

                # Appearances
                app = dff.groupby('source_product_id')['scrape_date'].nunique().reset_index(name='days_appeared')
                all7 = len(app[app['days_appeared'] == 7])
                st.metric("Products Appeared on All 7 Days", f"{all7:,}")

                st.info("If recalculated figures differ from reference (715/48/252/415/314/378/469), the difference is reported by calculation from filtered data - old values are not forced.")

                # Largest decreases/increases
                fl['change'] = fl['current_price_num_last'] - fl['current_price_num_first']
                col_dec, col_inc = st.columns(2)
                with col_dec:
                    dec = fl.sort_values('change').head(10).merge(dff[['source_product_id', 'product_name', 'brand_clean']].drop_duplicates('source_product_id'), on='source_product_id', how='left')
                    st.subheader("Largest Price Decreases")
                    showd = dec[['product_name', 'brand_clean', 'current_price_num_first', 'current_price_num_last', 'change']].copy()
                    showd['First (USD)'] = showd['current_price_num_first'].apply(format_usd)
                    showd['Last (USD)'] = showd['current_price_num_last'].apply(format_usd)
                    showd['Change (USD)'] = showd['change'].apply(format_usd)
                    st.dataframe(showd[['product_name', 'brand_clean', 'First (USD)', 'Last (USD)', 'Change (USD)']], hide_index=True)
                with col_inc:
                    inc = fl.sort_values('change', ascending=False).head(10).merge(dff[['source_product_id', 'product_name', 'brand_clean']].drop_duplicates('source_product_id'), on='source_product_id', how='left')
                    st.subheader("Largest Price Increases")
                    showi = inc[['product_name', 'brand_clean', 'current_price_num_first', 'current_price_num_last', 'change']].copy()
                    showi['First (USD)'] = showi['current_price_num_first'].apply(format_usd)
                    showi['Last (USD)'] = showi['current_price_num_last'].apply(format_usd)
                    showi['Change (USD)'] = showi['change'].apply(format_usd)
                    st.dataframe(showi[['product_name', 'brand_clean', 'First (USD)', 'Last (USD)', 'Change (USD)']], hide_index=True)

                # Daily median movement
                med_day = dff.groupby('scrape_date', dropna=True)['current_price_num'].median().reset_index(name='median_price_usd')
                fig = px.line(med_day, x='scrape_date', y='median_price_usd', title='Daily Median Price Movement',
                              labels={'scrape_date': 'Date', 'median_price_usd': 'Median Price (USD)'})
                st.plotly_chart(fig, use_container_width=True)

                # Discount movement
                med_disc = dff.groupby('scrape_date', dropna=True)['discount_pct_num'].median().reset_index(name='median_discount_pct')
                fig = px.line(med_disc, x='scrape_date', y='median_discount_pct', title='Discount Movement (Median %)',
                              labels={'scrape_date': 'Date', 'median_discount_pct': 'Median Discount %'})
                st.plotly_chart(fig, use_container_width=True)

                # Visibility
                vis = app.sort_values('days_appeared', ascending=False).head(20).merge(dff[['source_product_id', 'product_name', 'brand_clean']].drop_duplicates('source_product_id'), on='source_product_id', how='left')
                st.subheader("Product Visibility (Days Appeared)")
                st.dataframe(vis[['product_name', 'brand_clean', 'days_appeared']], hide_index=True)

    with tabs[4]:
        st.subheader("Brands & Product Table")
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if 'brand_clean' in dff.columns:
                top_br = dff.drop_duplicates('source_product_id')['brand_clean'].value_counts().head(10).reset_index()
                top_br.columns = ['brand', 'unique_products']
                fig = px.bar(top_br, x='brand', y='unique_products', title='Top 10 Brands by Unique Product Count',
                             labels={'brand': 'Brand', 'unique_products': 'Unique Products'})
                st.plotly_chart(fig, use_container_width=True)
        with col_b2:
            if 'category' in dff.columns and 'brand_clean' in dff.columns:
                br_cat = dff.drop_duplicates(subset=['source_product_id', 'category'])['category'].value_counts().to_frame()
                # simpler: count brands per cat
                br_cat = dff.groupby(['category', 'brand_clean'], dropna=True)['source_product_id'].nunique().reset_index()
                # show brand counts per category summary
                br_cnt_cat = br_cat.groupby('category')['brand_clean'].nunique().reset_index(name='brand_count')
                fig = px.bar(br_cnt_cat, x='category', y='brand_count', title='Brand Counts by Category',
                             labels={'category': 'Category', 'brand_count': 'Number of Brands'})
                st.plotly_chart(fig, use_container_width=True)

        st.subheader("Searchable Product Table")
        table_cols = ['scrape_date', 'product_name', 'brand_clean', 'category', 'current_price_num',
                      'old_price_num', 'discount_pct_num', 'rating_num', 'review_count_num', 'product_url']
        avail = [c for c in table_cols if c in dff.columns]
        tbl = dff[avail].copy()
        # Rename for display
        rename_map = {
            'scrape_date': 'Collection Date',
            'product_name': 'Product Name',
            'brand_clean': 'Brand',
            'category': 'Category',
            'current_price_num': 'Price (USD)',
            'old_price_num': 'Old Price (USD)',
            'discount_pct_num': 'Discount %',
            'rating_num': 'Rating',
            'review_count_num': 'Review Count',
            'product_url': 'Product URL',
        }
        tbl = tbl.rename(columns=rename_map)
        # Format
        if 'Price (USD)' in tbl:
            tbl['Price (USD)'] = tbl['Price (USD)'].apply(format_usd)
        if 'Old Price (USD)' in tbl:
            tbl['Old Price (USD)'] = tbl['Old Price (USD)'].apply(format_usd)
        if 'Discount %' in tbl:
            tbl['Discount %'] = tbl['Discount %'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else '—')
        if 'Rating' in tbl:
            tbl['Rating'] = tbl['Rating'].apply(lambda x: f"{x:.1f}" if pd.notna(x) else '—')
        if 'Review Count' in tbl:
            tbl['Review Count'] = tbl['Review Count'].apply(lambda x: f"{int(x):,}" if pd.notna(x) else '—')
        st.dataframe(tbl, use_container_width=True, hide_index=True)

        # Download
        csv_out = dff[avail].copy().rename(columns=rename_map)
        if 'Price (USD)' in csv_out:
            csv_out['Price (USD)'] = csv_out['Price (USD)'].apply(lambda x: round(float(x), 2) if pd.notna(x) else '')
        if 'Old Price (USD)' in csv_out:
            csv_out['Old Price (USD)'] = csv_out['Old Price (USD)'].apply(lambda x: round(float(x), 2) if pd.notna(x) else '')
        st.download_button(
            label="Download Filtered Data (CSV)",
            data=csv_out.to_csv(index=False).encode('utf-8'),
            file_name="jumia_nigeria_filtered.csv",
            mime="text/csv",
        )

    with tabs[5]:
        st.subheader("Kenya vs Nigeria (Optional)")
        kenya_phones = Path('product_level_phones_tablets_usd.csv')
        matched = Path('matched_products_usd.csv')
        if kenya_phones.exists() and matched.exists():
            st.success("Comparison files found. (Implementation simplified - showing availability.)")
            st.markdown("""
            - Comparison is narrower than full Nigeria study.
            - Overall country medians affected by product mix.
            - Matched products give fairer comparison.
            - Typical matched Nigerian listing was approx ~2.4% cheaper (as per reference).
            - This does not prove every Nigerian product is cheaper.
            """)
        else:
            st.warning("Optional comparison tab skipped: source files (product_level_phones_tablets_usd.csv, matched_products_usd.csv) not found locally.")

    st.markdown("---")
    st.markdown("**Academic dashboard created for DSC2107 Data Mining and Wrangling. Results describe observed catalogue listings and not completed sales.**")


if __name__ == '__main__':
    main()
