import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

API_KEY = 'c86b53fe-d972-44c4-8fdf-50b932be9160'
URL = f"https://elite.finviz.com/export.ashx?[allYourFilters]&auth={API_KEY}"
response = requests.get(URL)
with open("export.csv", "wb") as file:
    file.write(response.content)

df = pd.read_csv("export.csv")
print(df.head())

# Filter for technology stocks
tech_stocks = df[df['Sector'] == 'Technology']
print(tech_stocks.head())

# Basic Visualization: Plot stock price distribution
plt.hist(df['Price'], bins=20)
plt.title("Stock Price Distribution")
plt.xlabel("Price")
plt.ylabel("Frequency")
plt.show()



# Group data by sector and summarize
sector_summary = df.groupby('Sector').agg({
    'Price': ['mean', 'median', np.std],
    'Volume': ['sum', 'mean']
})
print(sector_summary)

# Yearly analysis if date information is available
if 'Date' in df.columns:
    df['Year'] = pd.to_datetime(df['Date']).dt.year
    yearly_data = df.groupby(['Year', 'Sector']).agg({
        'Price': ['mean', 'max'],
        'Volume': 'sum'
    })
    print(yearly_data)


# Visualize price distributions across sectors
plt.figure(figsize=(10, 6))
sns.boxplot(x='Sector', y='Price', data=df)
plt.xticks(rotation=45)
plt.title('Price Distribution by Sector')
plt.show()


if 'Date' in df.columns:
    tech_trend = df[df['Sector'] == 'Technology']
    tech_trend.set_index(pd.to_datetime(tech_trend['Date']), inplace=True)
    tech_trend['Price'].plot(title='Technology Stock Price Trend Over Time')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.show()

# Correlation Analysis
if {'Price', 'P/E', 'Volume', 'Market Cap'}.issubset(df.columns):
    financial_metrics = df[['Price', 'P/E', 'Volume', 'Market Cap']]  
    correlation_matrix = financial_metrics.corr()
    print(correlation_matrix)

    sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm')
    plt.title('Correlation Matrix of Financial Metrics')
    plt.show()


sector_summary.to_csv('sector_summary.csv')
if 'Year' in df.columns:
    yearly_data.to_csv('yearly_data.csv')


