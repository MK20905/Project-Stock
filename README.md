# Stock Screener Dashboard

This project provides an interactive stock screening and analysis dashboard built with Dash. It combines real-time market snapshots from Finviz and custom historical return calculations from Yahoo Finance, empowering users to:

- Quickly scan live market data with filtering, sorting, and conditional highlights.  
- Define any time interval and lookback period to calculate percentage returns on selected tickers.  
- Drill down into individual stock performance with interactive charts and key summary metrics.

---

## What This App Does

1. **Fetches Current Market Data**  
   - Pulls a warm snapshot of stock fundamentals (price, P/E, market cap, etc.) directly from Finviz Elite’s private CSV export.  
   - Caches the results for a short duration (10 minutes) to reduce redundant requests and remain responsive.

2. **Displays a Master Screener Table**  
   - Presents the Finviz data in a clean, filterable Dash DataTable.  
   - Highlights positive/negative price moves in green/red, with stronger coloring for moves beyond ±5%.  
   - Supports text search, column sorting, pagination, and auto-refresh options.

3. **Calculates Custom Historical Returns**  
   - Provides UI controls where users choose an **interval** (e.g. daily, hourly, minute) and **period** (e.g. 1 month, 6 months, 1 year).  
   - Limits the number of tickers processed at once (default 20) for performance and courtesy to Yahoo’s servers.  
   - Uses the `yfinance` library to pull OHLCV data from Yahoo Finance, handling any unavailable granularities with graceful fallbacks.  
   - Computes the percentage change from the first open price to the latest close price and displays it as **Custom Change** alongside the live data.

4. **Enables Deep Dive into Individual Stocks**  
   - Users click any ticker in the screener to navigate to a dedicated detail page.  
   - Shows an interactive Plotly chart of historical prices and overlays summary statistics like total return and volatility.  
   - Offers a seamless back link to return to the main screener.

---

## Key Components

- **`app_custom_change.py`**  
  Core dashboard combining Finviz snapshots, caching logic, custom return calculations, and the main DataTable layout and callbacks.

- **`app_details_page.py`**  
  Detail view logic: listens for ticker clicks, fetches historical data, and renders time series charts with performance metrics.

- **`fetch_finviz_data()`**  
  Handles HTTP GET to the Finviz CSV endpoint, parses and sanitizes data, and caches it using Flask-Caching.

- **`fetch_historical_data()` & `calculate_stock_change()`**  
  Leverage Yahoo Finance via `yfinance` to retrieve past prices and compute custom return percentages.

- **Dash Callbacks**  
  Power the interactivity: refreshing data, applying custom timeframes, sorting, filtering, and navigating to detail pages.

---

## Usage

1. Install dependencies:  
   ```bash
   pip install dash flask-caching pandas requests yfinance plotly
   ```
2. Configure your Finviz Elite URL in `app_custom_change.py`.  
3. Run the dashboard:  
   ```bash
   python app_custom_change.py
   ```
4. Open `http://127.0.0.1:8050` in your browser.  
5. Filter or search in the main table, set your desired interval & period, click **Calculate Custom Change**, and click tickers for detailed charts.

---

## Why This Matters

- **Speed & Convenience**: Instantly scan fundamental metrics across hundreds of tickers without manual data exports.  
- **Flexibility**: Choose any historical window to measure returns—daily, intraday, or custom.  
- **Insightful Visualization**: Seamlessly transition from a broad screener view to deep individual analysis in one app.

---

## License

This project is provided under the MIT License. See [LICENSE](LICENSE) for details.

*End of README*

