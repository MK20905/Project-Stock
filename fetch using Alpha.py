import requests
import pandas as pd
from datetime import datetime, timedelta

def get_intraday_data(symbol, interval="1min", api_key="YUL7IQ0LOA5MQSUK"):
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={symbol}&interval={interval}&apikey={api_key}&datatype=json"
    response = requests.get(url)
    data = response.json()

    if "Time Series" in data:
        time_series = data[f'Time Series ({interval})']
        df = pd.DataFrame(time_series).T
        df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        df.index = pd.to_datetime(df.index)
        df = df.sort_index()  # Sorting data by index (ascending time)
        return df
    else:
        print(f"Error fetching data for {symbol}: {data}")
        return None

if __name__ == "__main__":
    symbol = "AAPL"  # Example stock ticker
    api_key = "YUL7IQ0LOA5MQSUK"  # Replace with your actual Alpha Vantage API key
    intraday_data = get_intraday_data(symbol, "1min", api_key)

    if intraday_data is not None:
        print(intraday_data.head())  # Display the first few rows

