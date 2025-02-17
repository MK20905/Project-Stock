import dash
from dash import dcc, html, Input, Output, dash_table
import pandas as pd
import requests
from io import StringIO
from flask_caching import Cache
import plotly.graph_objs as go
import yfinance as yf

app = dash.Dash(__name__, suppress_callback_exceptions=True)
cache = Cache(app.server, config={'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 600})

finviz_url = "https://elite.finviz.com/export.ashx?v=111&f=allYourFilters&auth=b5d3db9b-199c-46fc-a163-b75245047e62"

@cache.memoize(timeout=600) 
def fetch_finviz_data():
    headers = {
        "User -Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(finviz_url, headers=headers)
    
    if response.status_code == 200:
        try:
            df = pd.read_csv(StringIO(response.text))
            df.columns = df.columns.map(str)  # Ensure all column names are strings
            return df
        except Exception as e:
            return pd.DataFrame({"Error": [f"Failed to parse data: {e}"]})
    elif response.status_code == 429:
        return pd.DataFrame({"Error": ["Rate limit exceeded. Please try again later."]})
    else:
        return pd.DataFrame({"Error": [f"Failed to fetch data. Status code: {response.status_code}"]})

def fetch_detailed_stock_data(ticker_symbol):
    stock = yf.Ticker(ticker_symbol)
    data = {
        "Index": stock.info.get("index", "N/A"),
        "Market Cap": stock.info.get("marketCap", "N/A"),
        "P/E": stock.info.get("trailingPE", "N/A"),
        "Forward P/E": stock.info.get("forwardPE", "N/A"),
        "EPS (ttm)": stock.info.get("trailingEps", "N/A"),
        "EPS (next Y)": stock.info.get("forwardEps", "N/A"),
        "EPS Growth": stock.info.get("earningsGrowth", "N/A"),
        "Revenue": stock.info.get("totalRevenue", "N/A"),
        "Operating Margin": stock.info.get("operatingMargins", "N/A"),
        "ROE": stock.info.get("returnOnEquity", "N/A"),
        "Debt/Equity": stock.info.get("debtToEquity", "N/A"),
        "Beta": stock.info.get("beta", "N/A"),
        "Volume": stock.info.get("regularMarketVolume", "N/A"),
        "52 Week High": stock.info.get("fiftyTwoWeekHigh", "N/A"),
        "52 Week Low": stock.info.get("fiftyTwoWeekLow", "N/A"),
        "Target Price": stock.info.get("targetMeanPrice", "N/A")
    }
    return pd.DataFrame(data.items(), columns=["Metric", "Value"])

def fetch_historical_data(ticker_symbol, interval):
    if interval in ['1m', '3m', '5m', '30m', '1h']:
        period = '7d'
    elif interval == '1d':
        period = '1mo'
    elif interval == '1w':
        period = '6mo'
    elif interval == '1M':
        period = '1y'
    else:
        period = '1y'  # Default to 1 year for any other case

    stock = yf.Ticker(ticker_symbol)
    df = stock.history(period=period, interval=interval)
    df.reset_index(inplace=True)

    df['SMA20'] = df['Close'].rolling(window=20).mean()
    df['SMA50'] = df['Close'].rolling(window=50).mean()
    df['SMA200'] = df['Close'].rolling(window=200).mean()

    return df

def main_page():
    df = fetch_finviz_data()
    if df.empty or "Error" in df.columns:
        return html.Div("No data available. Please check your Finviz configuration.", 
                        style={'textAlign': 'center', 'color': 'red'})

    return html.Div([
        html.Div([
            html.H1("Stock Screener", style={'textAlign': 'center', 'color': '#007BFF'}),
            html.Div([
                html.Button("Refresh Data", id="refresh-button", n_clicks=0, style={
                    'backgroundColor': '#007BFF', 'color': 'white', 'padding': '10px 20px', 'borderRadius': '5px', 'border': 'none', 'cursor': 'pointer'
                }),
                dcc.RadioItems(
                    id='refresh-interval-radio',
                    options=[
                        {'label': '10s', 'value': 10},
                        {'label': '1min', 'value': 60},
                        {'label': '3min', 'value': 180},  
                        {'label': '5min', 'value': 300},  
                        {'label': 'off', 'value': 0},
                    ],
                    value=0, 
                    labelStyle={'marginRight': '20px'}
                )
            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '20px'}),
            dcc.Interval(id='refresh-interval', interval=0, n_intervals=0),

            # Search Bar
            dcc.Input(id='search-input', type='text', placeholder='Search Ticker...', style={'marginBottom': '20px', 'width': '300px', 'padding': '10px', 'borderRadius': '5px', 'border': '1px solid #007BFF'}),

            html.Div([
                html.Label("Sort By:", style={'fontWeight': 'bold'}),
                dcc.Dropdown(
                    id='sort-by-dropdown',
                    options=[
                        {'label': col, 'value': col} for col in df.columns 
                    ],
                    value='Ticker',
                    style={'width': '45%', 'display': 'inline-block', 'marginRight': '10px'}
                ),
                dcc.RadioItems(
                    id='sort-order',
                    options=[
                        {'label': 'Ascending', 'value': 'asc'},
                        {'label': 'Descending', 'value': 'desc'}
                    ],
                    value='asc',
                    style={'display': 'inline-block'}
                )
            ], style={'marginBottom': '20px'}),

            # Main table
            dash_table.DataTable(
                id='main-table',
                columns=[{"name": col, "id": col} for col in df.columns],
                data=df.to_dict('records'),
                style_table={'overflowX': 'auto', 'border': '1px solid #007BFF'},
                style_cell={'textAlign': 'left', 'padding': '10px', 'border': '1px solid #f4f4f4'},
                style_header={'backgroundColor': '#007BFF', 'fontWeight': 'bold', 'color': 'white'},
                style_data_conditional=[
                    {
                        'if': {'column_id': 'Ticker'},
                        'cursor': 'pointer',
                        'color': 'blue',
                        'textDecoration': 'underline',
                    }
                ],
                page_size=10
            ),

            html.Div("Click on a ticker to view detailed analysis.",
                     style={'textAlign': 'center', 'marginTop': '10px'}),
        ], style={'padding': '20px', 'backgroundColor': '#f9f9f9', 'borderRadius': '10px', 'boxShadow': '0 4px 8px rgba(0,0,0,0.1)', 'margin': '20px'})
    ])

def detail_page(ticker_symbol):
    details_df = fetch_detailed_stock_data(ticker_symbol)

    return html.Div([
        html.H1(f"Details for {ticker_symbol}", style={'textAlign': 'center', 'color': '#007BFF'}),

        html.Label("Timeframe:", style={'fontWeight': 'bold'}),
        dcc.Dropdown(
            id='timeframe-dropdown',
            options=[
                {'label': '1 Minute', 'value': '1m'},
                {'label': '3 Minutes', 'value': '3m'},
                {'label': '5 Minutes', 'value': '5m'},
                {'label': '30 Minutes', 'value': '30m'},
                {'label': '1 Hour', 'value': '1h'},
                {'label': '1 Day', 'value': '1d'},
                {'label': '1 Week', 'value': '1w'},
                {'label': '1 Month', 'value': '1M'},
            ],
            value='1d',
            style={'width': '50%', 'marginBottom': '20px'}
        ),

        html.Label("Select SMAs to display:", style={'fontWeight': 'bold'}),
        dcc.Checklist(
            id='sma-options',
            options=[
                {'label': 'SMA20', 'value': 'SMA20'},
                {'label': 'SMA50', 'value': 'SMA50'},
                {'label': 'SMA200', 'value': 'SMA200'}
            ],
            value=['SMA20', 'SMA50'],  
            style={'marginBottom': '20px'}
        ),

        dcc.Graph(id='candlestick-chart'),

        html.H3("Volume", style={'textAlign': 'center'}),
        dcc.Graph(id='volume-chart'),

        html.H3("Stock Metrics", style={'textAlign': 'center'}),
        dash_table.DataTable(
            columns=[{"name": col, "id": col} for col in details_df.columns],
            data=details_df.to_dict('records'),
            style_table={'overflowX': 'auto', 'border': '1px solid #007BFF'},
            style_cell={'textAlign': 'left', 'padding': '10px', 'border': '1px solid #f4f4f4'},
            style_header={'backgroundColor': '#007BFF', 'fontWeight': 'bold', 'color': 'white'},
        ),

        # Link back to the main page
        dcc.Link('Back to Main Page', href='/', 
                 style={'textAlign': 'center', 'fontSize': '20px', 'color': '#007BFF'})
    ])

# ----------------------------------------------------------------------
# Callbacks
# ----------------------------------------------------------------------
@app.callback(
    [Output('main-table', 'data'),
     Output('refresh-interval', 'interval')],
    [Input('refresh-button', 'n_clicks'),
     Input('refresh-interval-radio', 'value'),
     Input('sort-by-dropdown', 'value'),
     Input('sort-order', 'value'),
     Input('search-input', 'value')],
    prevent_initial_call=True
)
def update_main_table(n_clicks, refresh_value, sort_by, sort_order, search_value):
    if refresh_value == 0:  
        interval = 0
    else:
        interval = refresh_value * 1000  
    df = fetch_finviz_data()
    
    # Filter by search input
    if search_value:
        df = df[df['Ticker'].str.contains(search_value, case=False, na=False)]

    ascending = (sort_order == 'asc')
    df = df.sort_values(by=sort_by, ascending=ascending)

    return df.to_dict('records'), interval

@app.callback(
    Output('url', 'pathname'),
    [Input('main-table', 'active_cell')],
    [dash.dependencies.State('main-table', 'data')]
)
def navigate_to_ticker(active_cell, table_data):
    if active_cell:
        row = active_cell['row']
        ticker_symbol = table_data[row]['Ticker'] 
        return f'/ticker/{ticker_symbol}' 
    return '/'

@app.callback(
    [Output('candlestick-chart', 'figure'), Output('volume-chart', 'figure')],
    [Input('timeframe-dropdown', 'value'), Input('sma-options', 'value')],
    Input('url', 'pathname')
)
def update_detail_page(timeframe, sma_options, pathname):
    if pathname.startswith('/ticker/'):
        ticker_symbol = pathname.split('/')[2]
        historical_data = fetch_historical_data(ticker_symbol, timeframe)

        candlestick_chart = go.Figure()
        candlestick_chart.add_trace(go.Candlestick(
            x=historical_data.index,
            open=historical_data['Open'],
            high=historical_data['High'],
            low=historical_data['Low'],
            close=historical_data['Close'],
            name='Candlestick'
        ))

        for sma in sma_options:
            candlestick_chart.add_trace(go.Scatter(
                x=historical_data.index, y=historical_data[sma],
                mode='lines', name=sma
            ))

        volume_chart = go.Figure()
        volume_chart.add_trace(go.Bar(
            x=historical_data.index, y=historical_data['Volume'],
            name='Volume'
        ))

        return candlestick_chart, volume_chart
    return {}, {}

@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    if pathname == '/' or pathname is None:
        return main_page()
    elif pathname.startswith('/ticker/'):
        ticker_symbol = pathname.split('/')[2]
        return detail_page(ticker_symbol)
    else:
        return html.H1("404: Page Not Found", style={'textAlign': 'center', 'color': 'red'})

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content', children=main_page())
])

if __name__ == '__main__':
    app.run_server(debug=True)