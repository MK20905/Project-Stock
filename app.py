import dash
from dash import dcc, html, Input, Output
import pandas as pd
from finvizfinance.quote import finvizfinance
import plotly.graph_objs as go
import logging

# Configure logging
logging.basicConfig(filename='stock_screener.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize the Dash app
app = dash.Dash(__name__)

# Define a list of tickers
tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'FB', 'NFLX', 'NVDA', 'BRK.B', 'JPM']

# Define a list of time frames
time_frames = [
    {'label': '1 Minute', 'value': '1min'},
    {'label': '5 Minutes', 'value': '5min'},
    {'label': '15 Minutes', 'value': '15min'},
    {'label': '1 Day', 'value': '1D'},
    {'label': '1 Week', 'value': '1W'},
    {'label': '1 Month', 'value': '1M'},
    {'label': '1 Year', 'value': '1Y'},
    {'label': '5 Years', 'value': '5Y'}
]

# Define the layout of the app
app.layout = html.Div([
    html.H1("Stock Screener Dashboard", style={'textAlign': 'center', 'color': '#333'}),
    dcc.Dropdown(
        id='ticker-dropdown',
        options=[{'label': ticker, 'value': ticker} for ticker in tickers],
        value='AAPL',
        style={'width': '50%', 'margin': 'auto'}
    ),
    dcc.Dropdown(
        id='timeframe-dropdown',
        options=time_frames,
        value='1D',
        style={'width': '50%', 'margin': 'auto'}
    ),
    html.Div(id='output-data', style={'margin': '20px'}),
    dcc.Graph(id='stock-graph', style={'height': '60vh'})
], style={'backgroundColor': '#f8f9fa', 'padding': '20px'})

# Function to fetch stock data
def fetch_data_for_ticker(ticker, timeframe):
    stock_data = finvizfinance(ticker)
    data = stock_data.ticker_fundament()
    if data:
        df = pd.DataFrame(data.items(), columns=['Metric', 'Value'])
        df['Timeframe'] = timeframe
        return df
    return None

# Callback to update the output data
@app.callback(
    Output('output-data', 'children'),
    Output('stock-graph', 'figure'),
    Input('ticker-dropdown', 'value'),
    Input('timeframe-dropdown', 'value')
)
def update_output(selected_ticker, selected_timeframe):
    # Fetch the latest data for the selected ticker and timeframe
    df = fetch_data_for_ticker(selected_ticker, selected_timeframe)
    
    if df is not None:
        # Create a simple table
        table = html.Table([
            html.Tr([html.Th(col) for col in df.columns])] +  # Header
            [html.Tr([html.Td(df.iloc[i][col]) for col in df.columns]) for i in range(len(df))]  # Data
        , style={'width': '100%', 'borderCollapse': 'collapse', 'margin': 'auto', 'backgroundColor': '#fff'})
        
        # Create an enhanced plot
        figure = go.Figure(data=[
            go.Bar(x=df['Metric'], y=df['Value'], marker_color='royalblue')
        ])
        figure.update_layout(
            title=f'{selected_ticker} Stock Data',
            xaxis_title='Metric',
            yaxis_title='Value',
            template='plotly_white',
            margin=dict(l=40, r=40, t=40, b=40)
        )
        return table, figure
    else:
        return "No data found.", {}

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)