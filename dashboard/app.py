import dash
from dash import dcc, html, dash_table, Input, Output
import plotly.express as px
import pandas as pd
from dashboard.data_provider import data_provider

app = dash.Dash(__name__, title="Nifty Bot Dashboard")

app.layout = html.Div([
    html.H1("🚀 Nifty Trading Bot Live Dashboard", style={'textAlign': 'center', 'color': '#2c3e50'}),

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
        html.H2("Live Positions & Recent Trades"),
        dash_table.DataTable(id="trades-table", page_size=10, style_table={'overflowX': 'auto'})
    ], style={'margin': '20px'}),

    dcc.Interval(id='interval-component', interval=10*1000, n_intervals=0) # Update every 10s
], style={'fontFamily': 'Arial, sans-serif', 'backgroundColor': '#f9f9f9', 'padding': '20px'})

@app.callback(
    [Output("win-rate", "children"),
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

    # Metrics
    win_rate = f"{summary['win_rate']}%"
    total_pnl = f"₹{summary['total_pnl']}"
    total_trades = str(summary['total_trades'])

    # PnL Chart
    pnl_fig = px.line(df_trades[::-1], x="timestamp", y="pnl", title="Equity Curve (Cumulative PnL)")
    if not df_trades.empty and 'pnl' in df_trades.columns:
        df_trades_sorted = df_trades.sort_values("timestamp")
        df_trades_sorted['cum_pnl'] = df_trades_sorted['pnl'].cumsum()
        pnl_fig = px.line(df_trades_sorted, x="timestamp", y="cum_pnl", title="Daily Equity Curve")

    # Signal Score Distribution
    sig_fig = px.histogram(df_signals, x="ai_score", title="AI Signal Quality Distribution")

    # Table
    table_data = df_trades.to_dict('records')
    table_cols = [{"name": i, "id": i} for i in df_trades.columns]

    return win_rate, total_pnl, total_trades, pnl_fig, sig_fig, table_data, table_cols

if __name__ == '__main__':
    app.run_server(debug=False, port=8050)
