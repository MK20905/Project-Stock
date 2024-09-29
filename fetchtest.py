import requests
from bs4 import BeautifulSoup
import pandas as pd
from finvizfinance.quote import finvizfinance

def get_stock_data_finviz(stock_ticker):
    try:
        stock = finvizfinance(stock_ticker)
        data = stock.ticker_fundament()
        return data
    except Exception as e:
        print(f"Error fetching data using finvizfinance for {stock_ticker}: {e}")
        return None

def get_stock_data_manual(stock_ticker):
    try:
        url = f"https://finviz.com/quote.ashx?t={stock_ticker}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            data = {}
            for row in soup.find_all('tr', class_='table-dark-row'):
                columns = row.find_all('td')
                if len(columns) == 12:
                    data[columns[0].text.strip()] = columns[1].text.strip()
            return data
        else:
            print(f"HTTP Error {response.status_code} for {stock_ticker}")
            return None
    except Exception as e:
        print(f"Error scraping data for {stock_ticker}: {e}")
        return None

if __name__ == "__main__":
    ticker = "AAPL"
    stock_data_finviz = get_stock_data_finviz(ticker)
    print(stock_data_finviz)

    stock_data_manual = get_stock_data_manual(ticker)
    if stock_data_manual:
        df = pd.DataFrame(stock_data_manual.items(), columns=['Metric', 'Value'])
        print(df)
    else:
        print(f"No data available for {ticker} using manual scraping.")
