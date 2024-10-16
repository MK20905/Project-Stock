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

def create_screener(tickers, criteria):
    screener_data = []
    for ticker in tickers:
        stock_data = StockData(ticker)
        stock_data_finviz = stock_data.get_data_finviz()
        stock_data_manual = stock_data.get_data_manual()
        
        if stock_data_finviz:
            df_finviz = pd.DataFrame(stock_data_finviz.items(), columns=['Metric', 'Value'])
        else:
            df_finviz = pd.DataFrame(columns=['Metric', 'Value'])
        
        if stock_data_manual:
            df_manual = pd.DataFrame(stock_data_manual.items(), columns=['Metric', 'Value'])
        else:
            df_manual = pd.DataFrame(columns=['Metric', 'Value'])
        
        # Merge the two dataframes
        df = pd.concat([df_finviz, df_manual])
        
        # Apply the screener criteria
        if criteria:
            for metric, value in criteria.items():
                df = df[df['Metric'] == metric]
                df = df[df['Value'] == value]
        
        # Add the ticker to the screener data
        screener_data.append((ticker, df))
    
    return screener_data

def log_screener_data(screener_data):
    for ticker, data in screener_data:
        print(f"Screener results for {ticker}:")
        print(data)

def main():
    tickers = ['AAPL', 'TSLA']
    criteria = {'P/E': '10.00', 'EPS (ttm)': '10.00'}  # Example criteria
    screener_data = create_screener(tickers, criteria)
    log_screener_data(screener_data)

if __name__ == "__main__":
    main()