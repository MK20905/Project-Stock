import requests
from bs4 import BeautifulSoup
import pandas as pd
from finvizfinance.quote import finvizfinance
from datetime import datetime, timedelta
import time

# Function to fetch stock data using finvizfinance package
def get_stock_data_finviz(stock_ticker):
    try:
        stock = finvizfinance(stock_ticker)
        return stock.ticker_fundament()
    except Exception as e:
        print(f"{datetime.now()} - Error fetching data using finvizfinance for {stock_ticker}: {e}")
        return None

# Function to manually scrape stock data from Finviz using BeautifulSoup
def get_stock_data_manual(stock_ticker):
    try:
        url = f"https://finviz.com/quote.ashx?t={stock_ticker}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Parse the table rows containing financial data
            return {row.find_all('td')[0].text.strip(): row.find_all('td')[1].text.strip()
                    for row in soup.find_all('tr', class_='table-dark-row') if len(row.find_all('td')) == 12}
        else:
            print(f"{datetime.now()} - HTTP Error {response.status_code} for {stock_ticker}")
            return None
    except Exception as e:
        print(f"{datetime.now()} - Error scraping data for {stock_ticker}: {e}")
        return None

# Function to log and display data for a list of stock tickers
def log_data_for_tickers(tickers):
    start_time = datetime.now()
    print(f"\n{start_time} - Fetching data...")
    total_runtime = 0
    
    # Loop through each stock ticker
    for ticker in tickers:
        iteration_start = datetime.now()
        
        print(f"\nFetching data for {ticker}...")
        
        # Fetch data using finvizfinance library
        stock_data_finviz = get_stock_data_finviz(ticker)
        if stock_data_finviz:
            print(f"All data using finvizfinance for {ticker}:")
            print(pd.DataFrame(stock_data_finviz.items(), columns=['Metric', 'Value']))
        else:
            print(f"No data available using finvizfinance for {ticker}.")
        
        # Fetch data by manually scraping Finviz website
        stock_data_manual = get_stock_data_manual(ticker)
        if stock_data_manual:
            print(f"All data using manual scraping for {ticker}:")
            print(pd.DataFrame(stock_data_manual.items(), columns=['Metric', 'Value']))
        else:
            print(f"No data available for {ticker} using manual scraping.")
        
        # Track and display runtime for each iteration
        iteration_end = datetime.now()
        iteration_runtime = (iteration_end - iteration_start).total_seconds()
        total_runtime += iteration_runtime
        print(f"Iteration runtime: {iteration_runtime:.2f} seconds")

    end_time = datetime.now()
    # Display total runtime for all tickers and schedule next run
    print(f"\nTotal runtime: {total_runtime:.2f} seconds")
    print(f"Next run scheduled at: {end_time + timedelta(seconds=total_runtime)}")

# Function to continuously fetch stock data at regular intervals
def fetch_data_at_interval(tickers, interval_minutes):
    while True:
        log_data_for_tickers(tickers)
        
        # Sleep for the interval period (in seconds) before next run
        sleep_time = interval_minutes * 60
        print(f"Sleeping for {sleep_time} seconds...")
        time.sleep(sleep_time)

# Main execution block
if __name__ == "__main__":
    # List of stock tickers to fetch data for
    tickers = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN"]
    
    # Interval in minutes between data fetches
    interval_minutes = 2
    
    # Start the data fetching process at the specified interval
    fetch_data_at_interval(tickers, interval_minutes)