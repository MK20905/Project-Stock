import requests
from bs4 import BeautifulSoup
import pandas as pd
from finvizfinance.quote import finvizfinance
from datetime import datetime, timedelta
import time

class StockData:
    def __init__(self, stock_ticker):
        self.stock_ticker = stock_ticker

    def get_data_finviz(self):
        try:
            stock = finvizfinance(self.stock_ticker)
            return stock.ticker_fundament()
        except finvizfinance.exceptions.FinvizError as e:
            print(f"{datetime.now()} - Finviz error for {self.stock_ticker}: {e}")
            return None
        except Exception as e:
            print(f"{datetime.now()} - Unexpected error for {self.stock_ticker}: {e}")
            return None

    def get_data_manual(self):
        try:
            url = f"https://finviz.com/quote.ashx?t={self.stock_ticker}"
            headers = {'User -Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                return {row.find_all('td')[0].text.strip(): row.find_all('td')[1].text.strip()
                        for row in soup.find_all('tr', class_='table-dark-row') if len(row.find_all('td')) == 12}
            else:
                print(f"{datetime.now()} - HTTP Error {response.status_code} for {self.stock_ticker}")
                return None
        except Exception as e:
            print(f"{datetime.now()} - Error scraping data for {self.stock_ticker}: {e}")
            return None

def log_data_for_tickers(tickers):
    start_time = datetime.now()
    print(f"\n{start_time} - Fetching data...")
    total_runtime = 0
    
    for ticker in tickers:
        iteration_start = datetime.now()
        
        print(f"\nFetching data for {ticker}...")
        
        stock_data = StockData(ticker)
        stock_data_finviz = stock_data.get_data_finviz()
        if stock_data_finviz:
            print(f"All data using finvizfinance for {ticker}:")
            print(pd.DataFrame(stock_data_finviz.items(), columns=['Metric', 'Value']))
        else:
            print(f"No data available using finvizfinance for {ticker}.")
        
        stock_data_manual = stock_data.get_data_manual()
        if stock_data_manual:
            print(f"All data using manual scraping for {ticker}:")
            print(pd.DataFrame(stock_data_manual.items(), columns=['Metric', 'Value']))
        else:
            print(f"No data available for {ticker} using manual scraping.")
        
        iteration_end = datetime.now()
        iteration_runtime = (iteration_end - iteration_start).total_seconds()
        total_runtime += iteration_runtime
        print(f"Iteration runtime: {iteration_runtime:.2f} seconds")

    end_time = datetime.now()
    print(f"\nTotal runtime: {total_runtime:.2f} seconds")
    print(f"Next run scheduled at: {end_time + timedelta(seconds=total_runtime)}")

def fetch_data_at_interval(tickers, interval_minutes):
    while True:
        log_data_for_tickers(tickers)
        sleep_time = interval_minutes * 60
        print(f"Sleeping for {sleep_time} seconds...")
        time.sleep(sleep_time)

if __name__ == "__main__":
    tickers = ['AAPL', 'TSLA']
    print("Tickers:", tickers)
    interval_minutes = 30
    fetch_data_at_interval(tickers, interval_minutes)