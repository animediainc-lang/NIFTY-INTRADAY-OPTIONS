import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import pandas as pd
from database.db_manager import DatabaseManager
from app_config.config_loader import ConfigLoader

app = dash.Dash(__name__, title="Multi-Agent Nifty Options Dashboard")
db = DatabaseManager()
config = ConfigLoader()

app.layout = html.Div(style={"backgroundColor": "#1e1e2f", "color": "#ffffff", "fontFamily": "Segoe UI, sans-serif", "padding": "20px"}, children=[

    # Header
    html.Div(style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "borderBottom": "1px solid #333", "paddingBottom": "10px"}, children=[
        html.H1("🤖 Multi-Agent Nifty AI Trading Engine", style={"margin": "0", "color": "#00d2ff"}),
        html.Div(children=[
            html.Span("MODE: ", style={"fontWeight": "bold"}),
            html.Span(f"{config.get('system.environment', 'PAPER').upper()}", style={
                "backgroundColor": "#28a745" if config.get('system.environment') == "paper" else "#dc3545",
                "padding": "5px 12px",
                "borderRadius": "4px",
                "fontWeight": "bold"
            })
        ])
    ]),

    # Key Metrics Bar
    html.Div(style={"display": "flex", "gap": "20px", "marginTop": "20px"}, children=[
        html.Div(style={"flex": "1", "backgroundColor": "#27293d", "padding": "15px", "borderRadius": "8px"}, children=[
            html.H4("Capital Available", style={"margin": "0", "color": "#a9a9a9"}),
            html.H2(f"₹{config.get('trading.default_capital', 500000.0):,.2f}", style={"margin": "5px 0 0 0", "color": "#28a745"})
        ]),
        html.Div(style={"flex": "1", "backgroundColor": "#27293d", "padding": "15px", "borderRadius": "8px"}, children=[
            html.H4("Active Symbol", style={"margin": "0", "color": "#a9a9a9"}),
            html.H2("NIFTY 50", style={"margin": "5px 0 0 0", "color": "#00d2ff"})
        ]),
        html.Div(style={"flex": "1", "backgroundColor": "#27293d", "padding": "15px", "borderRadius": "8px"}, children=[
            html.H4("Max Risk Limit", style={"margin": "0", "color": "#a9a9a9"}),
            html.H2("1.0% / Trade", style={"margin": "5px 0 0 0", "color": "#ffc107"})
        ]),
        html.Div(style={"flex": "1", "backgroundColor": "#27293d", "padding": "15px", "borderRadius": "8px"}, children=[
            html.H4("Kill Switch Threshold", style={"margin": "0", "color": "#a9a9a9"}),
            html.H2("3.0% Drawdown", style={"margin": "5px 0 0 0", "color": "#dc3545"})
        ])
    ]),

    # Main Grid (Live Trades & Agent Debates)
    html.Div(style={"display": "flex", "gap": "20px", "marginTop": "20px"}, children=[

        # Recent Executed Trades
        html.Div(style={"flex": "1", "backgroundColor": "#27293d", "padding": "20px", "borderRadius": "8px"}, children=[
            html.H3("Recent Executed Trades", style={"marginTop": "0", "color": "#00d2ff"}),
            html.Div(id="trades-table-container")
        ]),

        # Agent Debate Reasoning Logs
        html.Div(style={"flex": "1", "backgroundColor": "#27293d", "padding": "20px", "borderRadius": "8px"}, children=[
            html.H3("Multi-Agent AI Debate Consensus", style={"marginTop": "0", "color": "#00d2ff"}),
            html.Div(id="debates-table-container")
        ])
    ]),

    dcc.Interval(id="interval-component", interval=5000, n_intervals=0) # Refresh every 5s
])

@app.callback(
    [Output("trades-table-container", "children"),
     Output("debates-table-container", "children")],
    [Input("interval-component", "n_intervals")]
)
def update_dashboard_data(n):
    # Fetch recent trades
    trades = db.get_recent_trades(limit=10)
    if trades:
        df_trades = pd.DataFrame(trades)[["trade_id", "symbol", "action", "quantity", "entry_price", "pnl", "status"]]
        trades_table = dash_table.DataTable(
            data=df_trades.to_dict('records'),
            columns=[{"name": i.upper(), "id": i} for i in df_trades.columns],
            style_header={'backgroundColor': '#1f1f2e', 'color': '#00d2ff', 'fontWeight': 'bold'},
            style_cell={'backgroundColor': '#27293d', 'color': '#ffffff', 'textAlign': 'center', 'border': '1px solid #333'}
        )
    else:
        trades_table = html.P("No trades executed yet.", style={"color": "#a9a9a9"})

    # Fetch debates
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT debate_id, timestamp, underlying_price, vix, pcr, confidence_score, vetoed_by_risk FROM agent_debates ORDER BY timestamp DESC LIMIT 10")
        debates = [dict(row) for row in cursor.fetchall()]

    if debates:
        df_debates = pd.DataFrame(debates)
        debates_table = dash_table.DataTable(
            data=df_debates.to_dict('records'),
            columns=[{"name": i.upper(), "id": i} for i in df_debates.columns],
            style_header={'backgroundColor': '#1f1f2e', 'color': '#00d2ff', 'fontWeight': 'bold'},
            style_cell={'backgroundColor': '#27293d', 'color': '#ffffff', 'textAlign': 'center', 'border': '1px solid #333'}
        )
    else:
        debates_table = html.P("No agent debates logged yet.", style={"color": "#a9a9a9"})

    return trades_table, debates_table

if __name__ == "__main__":
    app.run_server(debug=False, port=8050)
