import dash
from dash import dcc, html, Input, Output
import pandas as pd
import plotly.graph_objs as go
import os
import glob
import logging


logging.basicConfig(filename='stock_screener.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')


app = dash.Dash(__name__)

# Path to CSV data
data_dir = 'stock_data'  # Directory where CSVs are saved by stock_screener.py

# Function to load CSV data from the stock_data directory
def load_stock_data():
    csv_files = glob.glob(os.path.join(data_dir, '*.csv'))
    stock_data = {}
    for file in csv_files:
        ticker = os.path.basename(file).split('_')[0]
        df = pd.read_csv(file)
        if ticker not in stock_data:
            stock_data[ticker] = []
        stock_data[ticker].append((file, df))
    return stock_data

# Load stock data
stock_data = load_stock_data()

# Define the layout of the app
app.layout = html.Div([
    html.H1("Stock Screener Dashboard", style={'textAlign': 'center', 'color': '#333'}),
    dcc.Input(id='ticker-input', type='text', placeholder='Enter tickers separated by commas', style={'width': '50%', 'margin': 'auto'}),
    html.Button('Fetch Data', id='fetch-button', n_clicks=0, style={'display': 'block', 'margin': '20px auto'}),
    html.Div(id='output-data', style={'margin': '20px'}),
    dcc.Graph(id='stock-graph', style={'height': '60vh'})
], style={'backgroundColor': '#f8f9fa', 'padding': '20px'})

# Callback to update the output data
@app.callback(
    [Output('output-data', 'children'),
     Output('stock-graph', 'figure')],
    [Input('fetch-button', 'n_clicks')],
    [Input('ticker-input', 'value')]
)
def update_output(n_clicks, ticker_input):
    if n_clicks > 0 and ticker_input:
        tickers = [ticker.strip().upper() for ticker in ticker_input.split(',')]
        all_data = []
        
        for ticker in tickers:
            if ticker in stock_data:
                # Select the latest data for the selected ticker
                latest_file, df = max(stock_data[ticker], key=lambda x: os.path.getctime(x[0]))
                all_data.append((ticker, df))
        
        if all_data:
            tables = []
            for ticker, df in all_data:
                table = html.Table([
                    html.Tr([html.Th(col) for col in df.columns])] +  # Header
                    [html.Tr([html.Td(df.iloc[i][col]) for col in df.columns]) for i in range(len(df))],  # Data
                    style={'width': '100%', 'borderCollapse': 'collapse', 'margin': 'auto', 'backgroundColor': '#fff'}
                )
                tables.append(html.Div([html.H3(f"Data for {ticker}"), table], style={'marginBottom': '20px'}))
            
            # Create an enhanced plot for the first ticker
            first_ticker, first_df = all_data[0]
            figure = go.Figure(data=[
                go.Bar(x=first_df['Metric'], y=first_df['Value'], marker_color='royalblue')
            ])
            figure.update_layout(
                title=f'{first_ticker} Stock Data',
                xaxis_title='Metric',
                yaxis_title='Value',
                template='plotly_white',
                margin=dict(l=40, r=40, t=40, b=40)
            )
            
            return tables, figure
        else:
            return "No data found.", {}
    return "Please enter tickers and click Fetch Data.", {}

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
