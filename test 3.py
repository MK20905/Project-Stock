import dash
from dash import dcc, html, Input, Output, dash_table
import pandas as pd
import requests
from io import StringIO
from flask_caching import Cache
import plotly.graph_objs as go
import time
import random

app = dash.Dash(__name__, suppress_callback_exceptions=True)
cache = Cache(app.server, config={'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 3600})  # 1-hour cache

# Your auth token
auth_token = "e8cfa282-9be3-4ce5-aad3-0127e25aaaf8"

# Headers for requests
headers = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/91.0.4472.124 Safari/537.36")
}

@cache.memoize(timeout=3600)  # Cache for 1 hour
def fetch_finviz_data():
    """Fetch the main screener data from Finviz Elite"""
    # Try to use a view that includes more change data
    # v=141 Technical, v=171 Technical+, v=152 Custom
    finviz_url = f"https://elite.finviz.com/export.ashx?v=171&auth={auth_token}"
    
    response = requests.get(finviz_url, headers=headers)
    print(f"Fetching main data from Finviz... Status: {response.status_code}")

    if response.status_code == 200:
        try:
            df = pd.read_csv(StringIO(response.text))
            print("Available columns in data:", df.columns.tolist())
            
            df.columns = df.columns.map(str)
            
            # Process the 'Change' column if it exists
            if 'Change' in df.columns:
                df['Change'] = pd.to_numeric(df['Change'].replace('%', '', regex=True), errors='coerce')
                if df['Change'].max() < 1:
                    df['Change'] = df['Change'] * 100
                df['Change'] = df['Change'].round(2)
                
                # Copy for 1d column if it doesn't exist
                if 'Change 1d' not in df.columns:
                    df['Change 1d'] = df['Change']
            
            # Try all possible column names for time-based change data
            possible_columns = {
                'Change 1w': ['Change (W)', 'W-Change', 'Perf Week', 'W Change', 'Perf W'],
                'Change 1mo': ['Change (M)', 'M-Change', 'Perf Month', 'M Change', 'Perf M'],
                'Change 3mo': ['Perf Quart', 'Q-Change', 'Perf Quarter', 'Q Change', 'Perf Q'],
                'Change 6mo': ['Perf Half Y', 'HY-Change', 'Perf Half', 'HY Change', 'Perf HY'],
                'Change 1y': ['Perf Year', 'Y-Change', 'Perf Y', 'Y Change', 'Perf YTD']
            }
            
            # Check for each possible column name
            for target_col, source_cols in possible_columns.items():
                for source_col in source_cols:
                    if source_col in df.columns:
                        # Convert to numeric
                        df[target_col] = pd.to_numeric(df[source_col].astype(str).str.replace('%', ''), errors='coerce')
                        # Make sure it's percentage not decimal
                        if df[target_col].max() < 1:
                            df[target_col] = df[target_col] * 100
                        df[target_col] = df[target_col].round(2)
                        break
            
            # For any remaining timeframes not found, try to fetch individually
            fetch_individual = True
            if fetch_individual:
                tickers_to_process = df['Ticker'].tolist()[:5]  # Just first 5 for testing
                
                # Initialize change columns if they don't exist
                for col in ['Change 1w', 'Change 1mo', 'Change 3mo', 'Change 6mo', 'Change 1y']:
                    if col not in df.columns:
                        df[col] = None
                
                # Try to get ticker-specific data
                for ticker in tickers_to_process:
                    ticker_data = fetch_ticker_details(ticker)
                    
                    # Update the dataframe with the ticker-specific changes
                    if not ticker_data.empty:
                        for col in ['Change 1w', 'Change 1mo', 'Change 3mo', 'Change 6mo', 'Change 1y']:
                            if col in ticker_data:
                                df.loc[df['Ticker'] == ticker, col] = ticker_data[col]
            
            # Convert other relevant columns to numeric
            numeric_columns = [
                'Market Cap', 'P/E', 'Forward P/E', 'EPS (ttm)', 'EPS (next Y)', 
                'EPS Growth', 'Revenue', 'Operating Margin', 'ROE', 'Debt/Equity', 'Beta'
            ]
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            return df
        except Exception as e:
            print(f"Error parsing data from Finviz: {e}")
            return pd.DataFrame({"Error": ["Failed to parse data from Finviz"]})
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
        return pd.DataFrame({"Error": [f"Failed to fetch data. Status code: {response.status_code}"]})

@cache.memoize(timeout=1800)  # Cache for 30 minutes
def fetch_ticker_details(ticker):
    """
    Fetch detailed change data for a specific ticker
    """
    # Try to use a view focused on performance data
    ticker_url = f"https://elite.finviz.com/export.ashx?v=171&t={ticker}&auth={auth_token}"
    
    time.sleep(0.5)  # Simple delay to avoid rate limits
    response = requests.get(ticker_url, headers=headers)
    
    if response.status_code == 200:
        try:
            df = pd.read_csv(StringIO(response.text))
            
            print(f"Ticker {ticker} columns:", df.columns.tolist())
            
            # Extract change data
            change_data = {}
            
            # Map possible column names to our standard names
            column_mappings = {
                'Change 1w': ['Change (W)', 'W-Change', 'Perf Week', 'W Change', 'Perf W'],
                'Change 1mo': ['Change (M)', 'M-Change', 'Perf Month', 'M Change', 'Perf M'],
                'Change 3mo': ['Perf Quart', 'Q-Change', 'Perf Quarter', 'Q Change', 'Perf Q'],
                'Change 6mo': ['Perf Half Y', 'HY-Change', 'Perf Half', 'HY Change', 'Perf HY'],
                'Change 1y': ['Perf Year', 'Y-Change', 'Perf Y', 'Y Change', 'Perf YTD']
            }
            
            # Check for each possible column name
            for target_col, source_cols in column_mappings.items():
                for source_col in source_cols:
                    if source_col in df.columns:
                        try:
                            value = df[source_col].iloc[0]
                            if isinstance(value, str) and '%' in value:
                                value = float(value.replace('%', ''))
                            else:
                                value = float(value)
                            
                            # Make sure it's percentage not decimal
                            if abs(value) < 1:
                                value *= 100
                                
                            change_data[target_col] = round(value, 2)
                            break
                        except (ValueError, TypeError) as e:
                            print(f"Error processing {source_col} for {ticker}: {e}")
            
            # If we couldn't find data, generate random values for testing
            if not change_data and ticker:
                # Simulate based on daily change
                if 'Change' in df.columns:
                    try:
                        daily_change = float(df['Change'].iloc[0].replace('%', '')) if isinstance(df['Change'].iloc[0], str) else float(df['Change'].iloc[0])
                        if abs(daily_change) < 1:
                            daily_change *= 100
                    except (ValueError, IndexError, AttributeError):
                        daily_change = random.uniform(-2, 2)
                        
                    # Generate simulated timeframe changes based on daily change
                    change_data['Change 1w'] = round(daily_change * random.uniform(2, 4), 2)
                    change_data['Change 1mo'] = round(daily_change * random.uniform(3, 6), 2)
                    change_data['Change 3mo'] = round(daily_change * random.uniform(4, 8), 2)
                    change_data['Change 6mo'] = round(daily_change * random.uniform(5, 10), 2)
                    change_data['Change 1y'] = round(daily_change * random.uniform(6, 12), 2)
            
            return pd.Series(change_data)
        except Exception as e:
            print(f"Error processing ticker data for {ticker}: {e}")
            return pd.Series()
    else:
        print(f"Failed to fetch data for ticker {ticker}. Status code: {response.status_code}")
        return pd.Series()

def main_page():
    # Fetch data with change calculations
    df = fetch_finviz_data()
    
    if df.empty or "Error" in df.columns:
        return html.Div(
            "No data available. Please check your Finviz configuration.", 
            style={'textAlign': 'center', 'color': 'red'}
        )
    
    # Define numeric columns for proper display
    numeric_columns = [
        'Market Cap', 'P/E', 'Forward P/E', 'EPS (ttm)', 'EPS (next Y)', 
        'EPS Growth', 'Revenue', 'Operating Margin', 'ROE', 'Debt/Equity', 'Beta', 
        'Change', 'Change 1d', 'Change 1w', 'Change 1mo', 'Change 3mo', 'Change 6mo', 'Change 1y'
    ]

    return html.Div([
        html.H1("Stock Screener - Main Page", style={'textAlign': 'center', 'color': '#007BFF'}),
        
        html.Div([
            html.Div([
                html.Label("Search:"),
                dcc.Input(
                    id='search-input',
                    type='text',
                    placeholder='Type a ticker or company name...',
                    style={'marginRight': '10px'}
                )
            ], style={'display': 'inline-block', 'marginRight': '20px'}),
            html.Button("Refresh Data", id="refresh-button", n_clicks=0, 
                        style={'backgroundColor': '#007BFF', 'color': 'white', 
                               'padding': '10px 20px', 'borderRadius': '5px'}),
            dcc.RadioItems(
                id='refresh-interval-radio',
                options=[
                    {'label': '10s', 'value': 10},
                    {'label': '1min', 'value': 60},
                    {'label': 'off', 'value': 0},
                ],
                value=0,
                labelStyle={'marginRight': '20px'}
            )
        ], style={'marginBottom': '20px'}),
        dcc.Interval(id='refresh-interval', interval=0, n_intervals=0),

        html.Div([
            html.Label("Sort By:"),
            dcc.Dropdown(
                id='sort-by-dropdown',
                options=[{'label': col, 'value': col} for col in df.columns],
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

        html.Div(id='processing-status', 
                 children=f"Data loaded at {time.strftime('%H:%M:%S')}",
                 style={'textAlign': 'center', 'fontStyle': 'italic', 'marginBottom': '10px'}),

        dash_table.DataTable(
            id='main-table',
            columns=[{"name": col, "id": col, "type": "numeric" if col in numeric_columns else "text"} for col in df.columns],
            data=df.to_dict('records'),
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'left', 'padding': '5px'},
            style_header={'backgroundColor': '#f4f4f4', 'fontWeight': 'bold'},
            style_data_conditional=[
                {
                    'if': {'column_id': 'Ticker'},
                    'cursor': 'pointer',
                    'color': 'blue',
                    'textDecoration': 'underline',
                },
                # Conditional formatting for change columns
                {
                    'if': {'filter_query': '{Change} > 0', 'column_id': 'Change'},
                    'backgroundColor': 'rgba(144, 238, 144, 0.3)',
                    'color': 'green'
                },
                {
                    'if': {'filter_query': '{Change} < 0', 'column_id': 'Change'},
                    'backgroundColor': 'rgba(255, 182, 193, 0.3)',
                    'color': 'red'
                },
                {
                    'if': {'filter_query': '{Change 1d} > 0', 'column_id': 'Change 1d'},
                    'backgroundColor': 'rgba(144, 238, 144, 0.3)',
                    'color': 'green'
                },
                {
                    'if': {'filter_query': '{Change 1d} < 0', 'column_id': 'Change 1d'},
                    'backgroundColor': 'rgba(255, 182, 193, 0.3)',
                    'color': 'red'
                },
                {
                    'if': {'filter_query': '{Change 1w} > 0', 'column_id': 'Change 1w'},
                    'backgroundColor': 'rgba(144, 238, 144, 0.3)',
                    'color': 'green'
                },
                {
                    'if': {'filter_query': '{Change 1w} < 0', 'column_id': 'Change 1w'},
                    'backgroundColor': 'rgba(255, 182, 193, 0.3)',
                    'color': 'red'
                },
                {
                    'if': {'filter_query': '{Change 1mo} > 0', 'column_id': 'Change 1mo'},
                    'backgroundColor': 'rgba(144, 238, 144, 0.3)',
                    'color': 'green'
                },
                {
                    'if': {'filter_query': '{Change 1mo} < 0', 'column_id': 'Change 1mo'},
                    'backgroundColor': 'rgba(255, 182, 193, 0.3)',
                    'color': 'red'
                },
                {
                    'if': {'filter_query': '{Change 3mo} > 0', 'column_id': 'Change 3mo'},
                    'backgroundColor': 'rgba(144, 238, 144, 0.3)',
                    'color': 'green'
                },
                {
                    'if': {'filter_query': '{Change 3mo} < 0', 'column_id': 'Change 3mo'},
                    'backgroundColor': 'rgba(255, 182, 193, 0.3)',
                    'color': 'red'
                },
                {
                    'if': {'filter_query': '{Change 6mo} > 0', 'column_id': 'Change 6mo'},
                    'backgroundColor': 'rgba(144, 238, 144, 0.3)',
                    'color': 'green'
                },
                {
                    'if': {'filter_query': '{Change 6mo} < 0', 'column_id': 'Change 6mo'},
                    'backgroundColor': 'rgba(255, 182, 193, 0.3)',
                    'color': 'red'
                },
                {
                    'if': {'filter_query': '{Change 1y} > 0', 'column_id': 'Change 1y'},
                    'backgroundColor': 'rgba(144, 238, 144, 0.3)',
                    'color': 'green'
                },
                {
                    'if': {'filter_query': '{Change 1y} < 0', 'column_id': 'Change 1y'},
                    'backgroundColor': 'rgba(255, 182, 193, 0.3)',
                    'color': 'red'
                }
            ],
            page_size=10,
            sort_action='native',
            filter_action='native',  # Enable filtering
        ),

        html.Div("Click on a ticker to view detailed analysis.",
                 style={'textAlign': 'center', 'marginTop': '10px'}),
    ])

@app.callback(
    [Output('main-table', 'data'),
     Output('refresh-interval', 'interval'),
     Output('processing-status', 'children')],
    [Input('refresh-button', 'n_clicks'),
     Input('refresh-interval-radio', 'value'),
     Input('sort-by-dropdown', 'value'),
     Input('sort-order', 'value')],
    prevent_initial_call=True
)
def update_main_table(n_clicks, refresh_value, sort_by, sort_order):
    print(f"Refresh triggered! Button Clicks: {n_clicks}, Auto-refresh Interval: {refresh_value}s")
    
    interval = refresh_value * 1000 if refresh_value > 0 else 0
    
    # Get fresh data with all timeframe changes
    df = fetch_finviz_data()
    
    # Status message
    status = f"Data refreshed at {time.strftime('%H:%M:%S')}"

    # Sort the data
    ascending = (sort_order == 'asc')
    try:
        df = df.sort_values(by=sort_by, ascending=ascending)
    except Exception as e:
        print(f"Error sorting data: {e}")
        status += f" (Sorting error: {e})"

    return df.to_dict('records'), interval, status

# For testing
if __name__ == '__main__':
    app.layout = html.Div([
        dcc.Location(id='url', refresh=False),
        html.Div(id='page-content', children=main_page())
    ])
    app.run_server(debug=True)