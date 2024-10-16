import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px

# Sample StockData class for demonstration purposes
class StockData:
    def __init__(self, ticker):
        self.ticker = ticker

    def get_data_finviz(self):
        # Simulate fetching data from Finviz
        data = {
            'Metric': ['Price', 'P/E', 'EPS (ttm)'],
            'Value': [150.00, 25.00, 6.00]
        }
        return pd.DataFrame(data)

    def get_data_manual(self):
        # Simulate fetching manual data
        data = {
            'Metric': ['Dividend', 'Market Cap'],
            'Value': [1.50, '2T']
        }
        return pd.DataFrame(data)

# Initialize the Dash app
app = dash.Dash(__name__)

# Define the layout of the app
app.layout = html.Div([
    html.H1('Stock Dashboard'),
    dcc.Dropdown(
        id='stock-ticker',
        options=[{'label': ticker, 'value': ticker} for ticker in ['AAPL', 'TSLA']],
        value='AAPL'
    ),
    html.Div(id='stock-data')
])

# Define the callback to update stock data
@app.callback(
    Output('stock-data', 'children'),
    [Input('stock-ticker', 'value')]
)
def update_stock_data(stock_ticker):
    print(f"Selected ticker: {stock_ticker}")
    stock_data = StockData(stock_ticker)
    
    # Retrieve data from Finviz and manual sources
    data_finviz = stock_data.get_data_finviz()
    data_manual = stock_data.get_data_manual()

    # Prepare Finviz data table
    if not data_finviz.empty:
        finviz_table = html.Table([
            html.Tr([html.Th(col) for col in data_finviz.columns]),
            *[html.Tr([html.Td(val) for val in row]) for row in data_finviz.values]
        ])
    else:
        finviz_table = html.Div("No Finviz data available.")

    # Prepare Manual data table
    if not data_manual.empty:
        manual_table = html.Table([
            html.Tr([html.Th(col) for col in data_manual.columns]),
            *[html.Tr([html.Td(val) for val in row]) for row in data_manual.values]
        ])
    else:
        manual_table = html.Div("No Manual data available.")

    return html.Div([
        html.H2('Finviz Data'),
        finviz_table,
        html.Hr(),
        html.H2('Manual Data'),
        manual_table
    ])

# Run the server
if __name__ == '__main__':
    app.run_server(debug=True)