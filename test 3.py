import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
from finvizfinance.quote import finvizfinance
from datetime import datetime, timedelta
import time
import logging
import concurrent.futures
import os

# Configure logging
logging.basicConfig(filename='stock_screener.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

class StockScreener:
    def __init__(self, symbol):
        self.symbol = symbol
        self.data = None
        self.manual_data = None

    def fetch_stock_data_finviz(self):
        try:
            stock = finvizfinance(self.symbol)
            self.data = stock.ticker_fundament()
            logging.info(f"Fetched data from Finviz for {self.symbol}.")
        except Exception as e:
            logging.error(f"Error fetching data from Finviz API for {self.symbol}: {e}")
            self.data = None

    def get_data_by_timeframe(self, timeframe='1D'):
        if self.data:
            df = pd.DataFrame(self.data.items(), columns=['Metric', 'Value'])
            df['Timeframe'] = timeframe
            return df
        return None

    def display_data(self, timeframe):
        if self.data is not None:
            print(f"\n{self.symbol} Stock Fundamentals ({timeframe} timeframe):")
            print(self.data)
        else:
            print("No data available to display.")

    def get_data_manual(self):
        try:
            url = f"https://finviz.com/quote.ashx?t={self.symbol}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                data = {}
                table = soup.find_all('table', class_='snapshot-table2')
                if table:
                    rows = table[0].find_all('tr')
                    for row in rows:
                        cols = row.find_all('td')
                        if len(cols) == 2:
                            key = cols[0].text.strip()
                            value = cols[1].text.strip()
                            data[key] = value
                self.manual_data = data
                return data
            else:
                logging.error(f"HTTP Error {response.status_code} for {self.symbol}")
                return None
        except Exception as e:
            logging.error(f"Error scraping data for {self.symbol}: {e}")
            return None

def fetch_data_for_ticker(ticker, timeframe):
    stock_data = StockScreener(ticker)
    stock_data.fetch_stock_data_finviz()
    stock_data.get_data_manual()
    
    results = []
    
    if stock_data.data is not None:
        filtered_data = stock_data.get_data_by_timeframe(timeframe)
        stock_data.display_data(timeframe)
        results.append((ticker, 'finvizfinance', filtered_data))
    else:
        logging.warning(f"No data available using finvizfinance for {ticker}.")
    
    if stock_data.manual_data:
        df_manual = pd.DataFrame(stock_data.manual_data.items(), columns=['Metric', 'Value'])
        print(f"All data using manual scraping for {ticker}:")
        print(df_manual)
        results.append((ticker, 'manual_scraping', df_manual))
    else:
        logging.warning(f"No data available for {ticker} using manual scraping.")
    
    return results

def log_data_for_tickers(tickers, timeframe):
    start_time = datetime.now()
    logging.info(f"Fetching data for tickers: {tickers}")

    all_data = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_ticker = {executor.submit(fetch_data_for_ticker, ticker, timeframe): ticker for ticker in tickers}
        for future in concurrent.futures.as_completed(future_to_ticker):
            ticker = future_to_ticker[future]
            try:
                data = future.result()
                all_data.extend(data)
            except Exception as exc:
                logging.error(f'{ticker} generated an exception: {exc}')

    save_data_to_csv(all_data, start_time)

    end_time = datetime.now()
    logging.info(f"Total runtime: {(end_time - start_time).total_seconds():.2f} seconds")

def save_data_to_csv(all_data, start_time):
    output_dir = 'stock_data'
    os.makedirs(output_dir, exist_ok=True)
    
    for ticker, method, data in all_data:
        if isinstance(data, pd.DataFrame):
            filename = f"{ticker}_{method}_data_{start_time.strftime('%Y%m%d_%H%M%S')}.csv"
            filepath = os.path.join(output_dir, filename)
            data.to_csv(filepath, index=False)
            logging.info(f"Data saved to {filepath}")

def fetch_data_at_interval(tickers, interval_minutes):
    while True:
        timeframe = input("Enter the timeframe for data (1h, 1d, 1w, 1m, 1y): ")
        if timeframe not in ['1h', '1d', '1w', '1m', '1y']:
            print("Invalid timeframe. Please enter a valid option.")
            continue
        log_data_for_tickers(tickers, timeframe)
        sleep_time = interval_minutes * 60
        logging.info(f"Sleeping for {sleep_time} seconds...")
        time.sleep(sleep_time)

if __name__ == "__main__":
    tickers = ['AAPL', 'MSFT', 'GOOGL']  
    print("Tickers:", tickers)
    interval_minutes = 30
    fetch_data_at_interval(tickers, interval_minutes)