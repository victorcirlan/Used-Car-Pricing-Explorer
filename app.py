from datetime import date

import kagglehub  # type: ignore[reportMissingImports]
import pandas as pd  # type: ignore[reportMissingImports]
import streamlit as st  # type: ignore[reportMissingImports]
import matplotlib.pyplot as plt  # type: ignore[reportMissingImports]
import seaborn as sns  # type: ignore[reportMissingImports]

st.set_page_config(
    page_title = "Used Car Pricing Explorer",
    page_icon = "🚗",
    layout = "wide"
)

st.title("Used Car Market Valuation & Pricing Explorer")
st.markdown(""" **Purpose:** This application helps budget-conscious consumers explore historical Craigslist used car asking prices and 
understand how prices vary by manufacturer, mileage, vehicle age, and state. It also provides summary statistics and correlation analysis for key variables.

**Main Questions:**
1. How are vehicle age and mileage associated with asking price?

2. How do median asking prices differ across manufacturers and states?

3. What are the summary statistics and correlations for price, mileage, and vehicle age?

**How to use:**
- Select manufacturer(s), state(s), maximum mileage, and maximum vehicle age using the sidebar filters. 
The application will update the visualizations and statistics based on your selections.
""")

@st.cache_data(ttl="1d")
def load_clean_data():
    path = kagglehub.dataset_download('austinreese/craigslist-carstrucks-data')
    data = pd.read_csv(f'{path}/vehicles.csv')
    cleaning_counts = [('Original imported dataset', len(data))]

    columns_to_drop = ['id', 'url', 'region_url', 'VIN', 'image_url', 'description', 'county', 'lat', 'long']
    data = data.drop(columns = [col for col in columns_to_drop if col in data.columns], errors = 'ignore')
    data['posting_date'] = pd.to_datetime(data['posting_date'], errors = 'coerce', utc = True)
    data = data.dropna(subset = ['price', 'year', 'odometer', 'manufacturer', 'posting_date'])
    cleaning_counts.append(('After removing missing records', len(data)))


    current_year = date.today().year
    
    data = data[
        (data['price'] >= 999) &
        (data['price'] <= 100000) &
        (data['odometer'] >= 1250) &
        (data['odometer'] <= 500000) &
        (data['year'] >= 1950) &
        (data['year'] <= current_year)
    ].copy()

    cleaning_counts.append(('After applying price, odometer, and year filters', len(data)))

    data.loc[:, 'manufacturer'] = data['manufacturer'].astype('string').str.strip().str.title()

    data.loc[:, 'state'] = (
        data['state'].astype('string').str.strip().str.upper().fillna('UNKNOWN')
    )

    for column in ['condition', 'transmission']:
        if column in data.columns:
            data.loc[:, column] = data[column].fillna('Unknown').astype('string').str.strip().str.title()

    data.loc[:, 'vehicle_age'] = (
        data['posting_date'].dt.year - data['year']
    )
    data = data[data['vehicle_age'].between(0, 100)].copy()
    cleaning_counts.append(('After filtering by vehicle age', len(data)))
    
    data =  data.drop_duplicates(subset = ['price', 'vehicle_age', 'year', 'odometer', 'manufacturer', 'model'])
    cleaning_counts.append(('After removing duplicates', len(data)))

    cleaning_summary = pd.DataFrame(cleaning_counts, columns = ['Stage', 'Records remaining'])

    cleaning_summary['Removed at this stage'] = (cleaning_summary['Records remaining'].shift(1).sub( cleaning_summary['Records remaining']).fillna(0).astype(int))

    original_count = cleaning_counts[0][1]
    cleaning_summary['Original records retained (%)'] = (cleaning_summary['Records remaining'] / max(original_count, 1) * 100).round(2)

    return data, cleaning_summary

df_clean, cleaning_summary = load_clean_data()
manufacturer_counts = df_clean['manufacturer'].value_counts()
if df_clean.empty:
    st.error("No listings remain after cleaning the dataset.")
    st.stop()

st.caption(f"Cleaned total listings: {len(df_clean):,}")
st.caption(
    f"Source: Kaggle hosted Craigslist used car listings dataset (https://www.kaggle.com/datasets/austinreese/craigslist-carstrucks-data) "
    f"One row represents one vehicle listing. "
)

st.sidebar.header("Filter Market Data")
selected_brands = st.sidebar.multiselect(
    "Select Car Brands",
    options = sorted(df_clean['manufacturer'].dropna().unique().tolist()),
    default = sorted(df_clean['manufacturer'].dropna().unique().tolist())
)

selected_state = st.sidebar.multiselect(
    "Select States",
    options = sorted(df_clean['state'].dropna().unique().tolist()),
    default = sorted(df_clean['state'].dropna().unique().tolist())
)

max_odometer = st.sidebar.slider(
    "Maximum Odometer (Miles)",
    min_value = int(df_clean['odometer'].min()),
    max_value = int(df_clean['odometer'].max()),
    value = int(df_clean['odometer'].max())
)

max_vehicle_age = st.sidebar.slider(
    "Maximum Vehicle Age (Years)",
    min_value = int(df_clean['vehicle_age'].min()),
    max_value = int(df_clean['vehicle_age'].max()),
    value = int(df_clean['vehicle_age'].max())
)

# Apply filters
filtered_df = df_clean[
    (df_clean['manufacturer'].isin(selected_brands)) &
    (df_clean['odometer'] <= max_odometer) &
    (df_clean['vehicle_age'] <= max_vehicle_age) &
    (df_clean['state'].isin(selected_state))
]

comparison_df = df_clean[
    (df_clean['manufacturer'].isin(selected_brands)) &
    (df_clean['odometer'] <= max_odometer) &
    (df_clean['vehicle_age'] <= max_vehicle_age)
].copy()

filtered_df = comparison_df.copy()

filtered_df = filtered_df[
    filtered_df['state'].isin(selected_state)
].copy()

# Making five tabs in streamlit for structural navigation
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Market Overview", "Price & Vehicle Age", "Interactive Explorer", "Statistical Analysis", "Limitations & Insights"])

with tab1:
    if filtered_df.empty:
        st.info("No listings match the selected filters.")
    else:
        metric_columns = st.columns(3)
        metric_columns[0].metric("Listings", f"{len(filtered_df):,}")
        metric_columns[1].metric("Median asking price", f"${filtered_df['price'].median():,.0f}")
        metric_columns[2].metric("Median mileage", f"{filtered_df['odometer'].median():,.0f} mi")

        median_prices = (
            filtered_df.groupby('manufacturer', as_index = False)['price']
            .median()
            .sort_values('price')
        )
        st.subheader("Median asking price by manufacturer")
        st.bar_chart(
            median_prices,
            x = 'manufacturer',
            y = 'price',
            x_label = "Manufacturer",
            y_label = "Median Asking Price ($)",
            alt = "Median asking price by manufacturer"
        )

        st.subheader("Median asking price by state")
        st.caption("This chart compares all states regardless of the selected state filters, but only includes states with at least 30 listings.")
        st.caption("Manufacturer, odometer, and vehicle age filters are applied to the data used for this chart.")
        state_prices = (
            comparison_df.dropna(subset = ['state'])
            .groupby('state', as_index = False)
            .agg(
                median_price = ('price', 'median'),
                listing_count = ('price', 'size')
            )
        )

        state_prices =state_prices[
            state_prices['state'] != 'UNKNOWN' 
        ]   

        state_prices = state_prices[state_prices['listing_count'] >= 30]

        if state_prices.empty:
            st.info("Not enough data to compare states.")
        else:
            top_states = (
                state_prices.nlargest(15, 'listing_count')
                .sort_values('median_price', ascending = False)
            )
            st.bar_chart(
                top_states,
                x="state",
                y="median_price",
                horizontal=True,
                x_label="State",
                y_label="Median Asking Price ($)",
                sort="-median_price",
                alt="Median asking price by state for the top 15 states by listing count")
        
            st.caption("Number of listings per state (only states with at least 30 listings are shown):")
        
        with st.expander("View supporting data"):
            st.dataframe(
                state_prices.sort_values('median_price', ascending = False).reset_index(drop = True),
                hide_index = True,
                )

with tab2:
    if filtered_df.empty:
        st.info("No listings match the selected filters.")
    else:
        st.subheader("Median Asking Price by Vehicle Age")
        selected_brand = st.selectbox(
            "Select a Manufacturer",
            options = sorted(filtered_df['manufacturer'].unique()),
            key = "age_chart_brand"
        )

        brand_data = filtered_df[filtered_df['manufacturer'] == selected_brand]

        age_prices = (
            brand_data.groupby('vehicle_age', as_index = False)
            .agg(
                median_price = ('price', 'median'),
                listing_count = ('price', 'size')
            )
            .sort_values('vehicle_age')
        )

        age_prices = age_prices[age_prices['listing_count'] >= 20]

        if age_prices.empty:
            st.info(f"No listings with at least 20 vehicles for {selected_brand}.")
        else:
            st.line_chart(
                age_prices,
                x = 'vehicle_age',
                y = 'median_price',
                x_label = "Vehicle Age (Years)",
                y_label = "Median Asking Price ($)",
                alt = f"Median asking price by vehicle age for {selected_brand}"
            )
            st.caption(f"Number of listings per vehicle age for {selected_brand} (only ages with at least 20 listings are shown):")

            with st.expander("View supporting data"):
                st.dataframe(
                    age_prices,
                    hide_index = True,
                )

with tab3:
    if filtered_df.empty:
        st.info("No listings match the selected filters.")
    else:
        chart_data = filtered_df.sample(n = min(len(filtered_df), 5000), random_state = 42)
        st.scatter_chart(
            chart_data,
            x = 'odometer',
            y = 'price',
            color = 'manufacturer',
            x_label = "Odometer (Miles)",
            y_label = "Asking Price ($)",
            # alt = "Vehicle asking price compared with odometer mileage"
        )
        st.dataframe(
            filtered_df[['state', 'manufacturer', 'model', 'year', 'price', 'odometer', 'vehicle_age']].head(100),
            hide_index = True
            # alt = "First 100 vehicle listings matching the selected filters"
        )

with tab4:
    st.subheader("Data Cleaning Summary")
    st.caption(
        "These counts reflect the cleaning of the original dataset, before sidebar filters." \
        "Only steps that remove records change the counts. The final count is the number of listings used in the analysis."
    )
    st.dataframe(cleaning_summary.style.format({
        'Records remaining': '{:,.0f}',
        'Removed at this stage': '{:,.0f}',
        'Original records retained (%) ': '{:,.2f}%'
    }),
    hide_index = True,
    width = 'stretch'
    )
    st.caption(
        "Duplicate detection matches price, age, year, odometer, manufacturer, and model; "
        "distinct listings may share those attributes. Standardizing text fields does not remove records."
    )

    st.divider()
    st.subheader('Summary Statistics and Correlation Analysis')
    if filtered_df.empty:
        st.info("No listings match the selected filters.")
    else:
        st.subheader("# of Cars per manufacturer")
        st.table(manufacturer_counts.head(10).rename_axis("Manufacturer").reset_index(name = "Count"))
        st.markdown("""
        The table displays the ten manufacturers with the most listings in the cleaned dataset.
        The full dataset contains many manufacturers with very few listings, which can skew the analysis. 
        The correlation analysis below uses all listings matching the currently selected filters.
        """)

        numeric_cols = ['price', 'odometer', 'vehicle_age']
        corr_data = filtered_df[numeric_cols].dropna()
        corr_matrix = corr_data.corr()

        summary_stats = corr_data.describe().T
        st.subheader("Summary Statistics")
        summary_stats = filtered_df[numeric_cols].describe().T
        summary_stats = summary_stats.rename(
            index = {
                'price': 'Asking Price ($)',
                'odometer': 'Odometer (miles)',
                'vehicle_age': 'Vehicle Age (years)'
            },
        columns = {
            'count': 'Count',
            'mean': 'Mean',
            'std': 'Std Deviation',
            'min': 'Minimum',
            '25%': '25th Percentile',
            '50%': 'Median',
            '75%': '75th Percentile',
            'max': 'Maximum'
        }
        )

        summary_stats = summary_stats[
            [
                'Count', 'Mean', 'Median', 'Std Deviation', 'Minimum', '25th Percentile', '75th Percentile', 'Maximum'
            ]]

        st.dataframe(
            summary_stats.style.format({
                'Count': '{:,.0f}',
                'Mean': '{:,.2f}',
                'Median': '{:,.2f}',
                'Std Deviation': '{:,.2f}',
                'Minimum': '{:,.2f}',
                '25th Percentile': '{:,.2f}',
                '75th Percentile': '{:,.2f}',
                'Maximum': '{:,.2f}'
            }),

            width = 'stretch')

        fig, ax = plt.subplots(figsize=(5, 4))
        sns.heatmap(
            corr_matrix,
            annot=True,
            cmap='coolwarm',
            vmin=-1,
            vmax=1,
            linewidths=0.5,
            fmt='.2f',
            ax=ax
        )
        ax.set_title('Correlation Heatmap: Price, Odometer, and Vehicle Age')
        fig.tight_layout()
        st.pyplot(
            fig,
            width = 500,
            alt="Correlation heatmap showing relationships among price, odometer, and vehicle age"
        )
        plt.close(fig)
    
        st.markdown("""
        The heatmap above shows the correlation coefficients between asking price, odometer mileage, and vehicle
        age. A negative correlation is observed between vehicle age and asking price, as well as between mileage and asking price.
        The correlation between vehicle age and mileage is positive, indicating that older vehicles tend to have higher mileage.

        When looking at the summary statistics, we can see that the median asking price is lower than the mean, 
        indicating a right-skewed distribution. We can see the right-skewed distribution in the scatterplot in the interactive explorer tab of the app. Given
        enough data, the skew of the scatterplot largely stays the same regardless of the filters applied.
        The median mileage and vehicle age also provide insights into the typical characteristics of vehicles in the dataset.
        Asking prices have a higher mean because of a few high-priced listings, while the median provides a better representation of the typical asking price.
        """)

    st.subheader("Correlation Coefficients")
    price_age_corr = corr_matrix.loc['price', 'vehicle_age']
    price_mileage_corr = corr_matrix.loc['price', 'odometer']
    age_mileage_corr = corr_matrix.loc['vehicle_age', 'odometer']

    col1, col2, col3 = st.columns(3)
    correlations = [
        (col1, "Price vs Vehicle Age", price_age_corr),
        (col2, "Price vs Mileage", price_mileage_corr),
        (col3, "Vehicle Age vs Mileage", age_mileage_corr)
    ]

    for column, label, value in correlations:
        if pd.notna(value):
            column.metric(label, f"{value:.2f}")
        else:
            column.metric(label, "N/A")

with tab5:
    st.subheader("How to read these results")
    st.markdown("""
    ***Key findings:***
    - There is a strong negative correlation between vehicle age and asking price, as well as between mileage and asking price.
    - The correlation between vehicle age and mileage is positive, indicating that older vehicles tend to have
    higher mileage.
    - The median asking price varies significantly across manufacturers and states, with some brands and regions commanding higher prices.
    - Summary statistics provide insights into the distribution of prices, mileage, and vehicle age, which can help consumers make informed decisions when buying a used car.

    ***Limitations:***
    - Prices are Craigslist asking prices, not confirmed sale prices.
    - Listings without price, year, odometer, or manufacturer are excluded.
    - Listings outside the selected price, mileage, and model-year bounds are excluded.
    - Duplicate detection uses price, year, mileage, manufacturer, and model; distinct listings can still look identical.
    - Vehicle condition, location, title status, and listing quality can affect price but are not controlled for here.
    - The dataset is limited to Craigslist listings, which may not represent the entire used car market.
    - The analysis is based on historical data and may not reflect current market conditions.
    - Comparing prices across vehicles of different ages does not directly measure how an individual vehicle depreciates over time. 
    """)


# to run Streamlit app, use the command: `streamlit run test.py` in the terminal.
# Set-Location "C:\Users\angel\OneDrive\Desktop\CMSE 830" 
# .\.venv\Scripts\python.exe -m streamlit run ".\streamlit test.py"

# 