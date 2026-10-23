# Used Car Pricing Explorer

## Project Purpose
A Streamlit data exploration application for examining historical Craigslist used-car asking prices.
This application helps budget-conscious consumers explore historical Craigslist used car asking prices and 
understand how prices vary by manufacturer, mileage, vehicle age, and state. It also provides summary statistics and correlation analysis for key variables.

## Main Questions:
1. How are vehicle age and mileage associated with asking price?

2. How do median asking prices differ across manufacturers and states?

3. What are the summary statistics and correlations for price, mileage, and vehicle age?

## DataSet
- Source: https://www.kaggle.com/datasets/austinreese/craigslist-carstrucks-data/data
- Unit of observation: One Craigslist vehicle listing before cleaning (not a completed sale or necessarily one unique vehicle)
- Data access: The application uses kagglehub to download the public dataset and reads `vehicles.csv`; the raw csv is not included in the repository
- Size: There are 26 columns with 426,880 rows in the original dataset.

## Application Features
|Tab| What it contains|
| --- | --- |
|Market Overview| Listing count, median price, median mileage, visualization of median price by manufacturer, visualization of median price for the 15 states with the highest qualifying listing counts.|
|Price & Vehicle Age| Median asking price by age for a selected manufacturer; age groups require at least 20 listings|
|Interactive Explorer| Mileage versus price scatterplot and a table of matching listings.|
|Statistical Analysis| Data-cleaning record counts, descriptive statistics, and correlation heatmap|
|Limitations & Insights| Interpretation guidance, findings, and analytical limitations.| 

## Data Preparation
The app reports how many records remain and how many are removed at each major cleaning step in the 4th tab of the app:
1. Read original dataset and discard columns not needed for analysis.
2. Convert `posting_date` to a date-time type, remove rows with missing price, year, odometer, manufacturer, or usable posting date.
3. Retain asking prices from **$999** to **$100,000**, odometer values from **1,250** to **500,000** miles, and year from **1950 through the year the app runs.**
4. Standardize manufacturer names and state codes, fill missing condition and transmission labels with `Unknown`.
5. Calculate **vehicle age = listing year - vehicle model year** and keep ages from **0 to 100 years**.
6. Remove repeated **attribute combinations** using price, vehicle age, year, odometer, manufacturer, and model. 

The filters are project-specific choices for exploratory analysis, **not universal rules** for determining whether a listing is valid.


## Setup and Run

This application requires Python 3.10+ and an internet
connection to download the Craigslist dataset from Kaggle.

### 1. Clone the Repository

```bash
git clone https://github.com/victorcirlan/Used-Car-Pricing-Explorer.git
cd Used-Car-Pricing-Explorer
```

### 2. Create a Virtual Environment (Optional)

```bash
python -m venv .venv
```

Activate the environment:

**Windows PowerShell:**
```powershell
.\.venv\Scripts\Activate.ps1
```

**macOS/Linux:**
```bash
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Run the Streamlit Application

```bash
python -m streamlit run app.py
```

The application will typically open at:

http://localhost:8501

The dataset is downloaded automatically using Kagglehub.
The application caches the cleaned data using Streamlit.


## Replication
The source dataset is downloaded programmatically rather than committed to GitHub. The precise results can depend on the dataset version returned by Kagglehub, library versions, and date-based year check. The version used when creating this application was Version 10. 

## Key Limitations
- Listing prices are seller asking prices, not transaction amounts.
- Variation by state or manufacturer may reflect differences in model mix, mileage, condition, and other attributes, rather than location or manufacturer alone.
- Craigslist listings may not represent the broader used-car market; records removed during cleaning may also bias the analyzed sample.
- Some charts suppress small groups (fewer than 20 listings for an age or fewer than 30 for a state).
- The analysis is based on historical data and may not reflect current market conditions.

## AI Disclosure

Generative AI assistance is documented separately in
[AI_DISCLOSURE.md](AI_DISCLOSURE.md). 
