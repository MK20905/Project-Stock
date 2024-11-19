from finvizfinance.quote import finvizfinance
stock = finvizfinance('TSLA')
stock.ticker_charts()
stock_fundament = stock.ticker_fundament()
stock_description = stock.ticker_description()
news_df = stock.ticker_news()

print("TSLA Fundamental Data:")
print(stock_fundament)

print("\nTSLA Company Description:")
print(stock_description)


print("\nRecent TSLA News:")
print(news_df)


# from finvizfinance.news import News

# fnews = News()
# all_news = fnews.get_news()
# print(all_news)
# all_news['blogs'].head()

# from finvizfinance.screener.overview import Overview

# foverview = Overview()
# filters_dict = {'Index':'S&P 500','Sector':'Basic Materials'}
# foverview.set_filter(filters_dict=filters_dict)
# df = foverview.screener_view()
# df.head()
# print(df)

# from finvizfinance.util import set_proxy

# proxies={'http': 'http://127.0.0.1:8080'}
# set_proxy(proxies)
