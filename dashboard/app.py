import dash
from dash import dcc, html, dash_table, Input, Output
import plotly.express as px
import pandas as pd
from dashboard.data_provider import data_provider
from app_config.config_loader import config

app = dash.Dash(__name__, title="Nifty Bot Dashboard")

app.layout = html.Div([
    # Header with Trading Mode
    html.Div([
        html.H1("🚀 Nifty Trading Bot Live Dashboard", style={'display': 'inline-block', 'marginRight': '20px'}),
        html.Div(id="trading-mode-indicator", style={
            'display': 'inline-block',
            'padding': '10px 20px',
            'borderRadius': '5px',
            'fontWeight': 'bold',
            'fontSize': '20px',
            'verticalAlign': 'middle'
        })
    ], style={'textAlign': 'center', 'color': '#2c3e50', 'backgroundColor': '#ecf0f1', 'padding': '10px'}),

    # Summary Cards
    html.Div([
        html.Div([html.H3("Win Rate"), html.P(id="win-rate")], className="card"),
        html.Div([html.H3("Total PnL"), html.P(id="total-pnl")], className="card"),
        html.Div([html.H3("Trades"), html.P(id="total-trades")], className="card"),
    ], style={'display': 'flex', 'justifyContent': 'space-around', 'margin': '20px'}),

    # Charts
    html.Div([
        dcc.Graph(id="pnl-chart", style={'width': '50%'}),
        dcc.Graph(id="signal-chart", style={'width': '50%'})
    ], style={'display': 'flex'}),

    # Tables
    html.Div([
        html.H2("Recent Activity"),
        dash_table.DataTable(id="trades-table", page_size=10, style_table={'overflowX': 'auto'})
    ], style={'margin': '20px'}),

    dcc.Interval(id='interval-component', interval=10*1000, n_intervals=0)
], style={'fontFamily': 'Arial, sans-serif', 'backgroundColor': '#f9f9f9', 'padding': '0px'})

@app.callback(
    [Output("trading-mode-indicator", "children"),
     Output("trading-mode-indicator", "style"),
     Output("win-rate", "children"),
     Output("total-pnl", "children"),
     Output("total-trades", "children"),
     Output("pnl-chart", "figure"),
     Output("signal-chart", "figure"),
     Output("trades-table", "data"),
     Output("trades-table", "columns")],
    [Input("interval-component", "n_intervals")]
)
def update_dashboard(n):
    summary = data_provider.get_performance_summary()
    df_trades = data_provider.get_trades()
    df_signals = data_provider.get_signals()

    # Mode Logic
    mode = config.get("trading.mode", "paper").upper()
    mode_color = "#f1c40f" if mode == "PAPER" else "#e74c3c" # Yellow for Paper, Red for Live
    mode_style = {
        'display': 'inline-block', 'padding': '10px 20px', 'borderRadius': '5px',
        'fontWeight': 'bold', 'fontSize': '20px', 'verticalAlign': 'middle',
        'backgroundColor': mode_color, 'color': 'white'
    }

    # Metrics
    win_rate = f"{summary['win_rate']}%"
    total_pnl = f"₹{summary['total_pnl']}"
    total_trades = str(summary['total_trades'])

    # PnL Chart
    pnl_fig = px.line(title="Cumulative PnL")
    if not df_trades.empty and 'pnl' in df_trades.columns:
        df_trades_sorted = df_trades.sort_values("timestamp")
        df_trades_sorted['cum_pnl'] = df_trades_sorted['pnl'].cumsum()
        pnl_fig = px.line(df_trades_sorted, x="timestamp", y="cum_pnl", title="Equity Curve")

    # Signal Score Distribution
    sig_fig = px.histogram(df_signals, x="ai_score", title="AI Signal Quality Distribution")

    # Table
    table_data = df_trades.to_dict('records')
    table_cols = [{"name": i, "id": i} for i in df_trades.columns]

    return mode, mode_style, win_rate, total_pnl, total_trades, pnl_fig, sig_fig, table_data, table_cols

if __name__ == '__main__':
    app.run_server(debug=False, port=8050)
