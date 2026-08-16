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

app.layout = html.Div(style={"backgroundColor": "#181924", "color": "#ffffff", "fontFamily": "Inter, Segoe UI, sans-serif", "padding": "24px"}, children=[

    # Header
    html.Div(style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "borderBottom": "1px solid #2a2c3d", "paddingBottom": "16px"}, children=[
        html.Div(children=[
            html.H1("🤖 Multi-Agent AI Nifty Options Dashboard", style={"margin": "0", "color": "#00d2ff", "fontSize": "26px", "fontWeight": "700"}),
            html.P("Real-time option chain analytics, agent consensus reasoning, and portfolio metrics", style={"margin": "4px 0 0 0", "color": "#8a8d9b", "fontSize": "14px"})
        ]),
        html.Div(children=[
            html.Span("TRADING MODE: ", style={"fontWeight": "600", "color": "#8a8d9b", "marginRight": "8px"}),
            html.Span(f"{config.get('system.environment', 'PAPER').upper()}", style={
                "backgroundColor": "#10b981" if config.get('system.environment') == "paper" else "#ef4444",
                "color": "#ffffff",
                "padding": "6px 14px",
                "borderRadius": "6px",
                "fontWeight": "700",
                "fontSize": "14px",
                "letterSpacing": "0.5px"
            })
        ])
    ]),

    # Key Metrics Cards Row
    html.Div(style={"display": "grid", "gridTemplateColumns": "repeat(4, 1fr)", "gap": "16px", "marginTop": "20px"}, children=[
        html.Div(style={"backgroundColor": "#202231", "padding": "18px", "borderRadius": "10px", "border": "1px solid #2a2c3d"}, children=[
            html.H4("Capital Available", style={"margin": "0", "color": "#8a8d9b", "fontSize": "13px", "fontWeight": "600"}),
            html.H2(f"₹{config.get('trading.default_capital', 500000.0):,.2f}", style={"margin": "8px 0 0 0", "color": "#10b981", "fontSize": "24px"})
        ]),
        html.Div(style={"backgroundColor": "#202231", "padding": "18px", "borderRadius": "10px", "border": "1px solid #2a2c3d"}, children=[
            html.H4("Active Symbol & Index", style={"margin": "0", "color": "#8a8d9b", "fontSize": "13px", "fontWeight": "600"}),
            html.H2("NIFTY 50", style={"margin": "8px 0 0 0", "color": "#00d2ff", "fontSize": "24px"})
        ]),
        html.Div(style={"backgroundColor": "#202231", "padding": "18px", "borderRadius": "10px", "border": "1px solid #2a2c3d"}, children=[
            html.H4("Max Risk / Trade", style={"margin": "0", "color": "#8a8d9b", "fontSize": "13px", "fontWeight": "600"}),
            html.H2("1.0% (₹5,000)", style={"margin": "8px 0 0 0", "color": "#f59e0b", "fontSize": "24px"})
        ]),
        html.Div(style={"backgroundColor": "#202231", "padding": "18px", "borderRadius": "10px", "border": "1px solid #2a2c3d"}, children=[
            html.H4("Kill Switch Limit", style={"margin": "0", "color": "#8a8d9b", "fontSize": "13px", "fontWeight": "600"}),
            html.H2("3.0% Drawdown", style={"margin": "8px 0 0 0", "color": "#ef4444", "fontSize": "24px"})
        ])
    ]),

    # Visual Charts Row (Equity Curve & Underlying Index Track)
    html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "20px", "marginTop": "20px"}, children=[
        html.Div(style={"backgroundColor": "#202231", "padding": "20px", "borderRadius": "10px", "border": "1px solid #2a2c3d"}, children=[
            html.H3("Portfolio Equity Curve (Cumulative PnL)", style={"marginTop": "0", "color": "#00d2ff", "fontSize": "16px"}),
            dcc.Graph(id="equity-curve-graph", style={"height": "280px"})
        ]),
        html.Div(style={"backgroundColor": "#202231", "padding": "20px", "borderRadius": "10px", "border": "1px solid #2a2c3d"}, children=[
            html.H3("Market Regime: India VIX & PCR Monitor", style={"marginTop": "0", "color": "#00d2ff", "fontSize": "16px"}),
            dcc.Graph(id="vix-pcr-graph", style={"height": "280px"})
        ])
    ]),

    # Main Tables Grid (Live Executed Trades & Multi-Agent Debate Logs)
    html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "20px", "marginTop": "20px"}, children=[

        # Recent Executed Trades Table
        html.Div(style={"backgroundColor": "#202231", "padding": "20px", "borderRadius": "10px", "border": "1px solid #2a2c3d"}, children=[
            html.H3("Executed Option Trades Log", style={"marginTop": "0", "color": "#00d2ff", "fontSize": "16px"}),
            html.Div(id="trades-table-container")
        ]),

        # Agent Debate Reasoning Logs Table
        html.Div(style={"backgroundColor": "#202231", "padding": "20px", "borderRadius": "10px", "border": "1px solid #2a2c3d"}, children=[
            html.H3("Multi-Agent AI Debate Consensus", style={"marginTop": "0", "color": "#00d2ff", "fontSize": "16px"}),
            html.Div(id="debates-table-container")
        ])
    ]),

    dcc.Interval(id="interval-component", interval=5000, n_intervals=0) # Auto-refresh every 5s
])

@app.callback(
    [Output("equity-curve-graph", "figure"),
     Output("vix-pcr-graph", "figure"),
     Output("trades-table-container", "children"),
     Output("debates-table-container", "children")],
    [Input("interval-component", "n_intervals")]
)
def update_dashboard_data(n):
    # 1. Equity Curve
    trades = db.get_recent_trades(limit=50)
    initial_cap = config.get("trading.default_capital", 500000.0)

    if trades:
        df_trades = pd.DataFrame(trades)
        df_trades = df_trades.sort_values("timestamp")
        df_trades["cum_pnl"] = df_trades["pnl"].cumsum()
        df_trades["equity"] = initial_cap + df_trades["cum_pnl"]
        x_vals = df_trades["timestamp"].tolist()
        y_vals = df_trades["equity"].tolist()
    else:
        x_vals = [pd.Timestamp.now().isoformat()]
        y_vals = [initial_cap]

    equity_fig = go.Figure(data=[
        go.Scatter(x=x_vals, y=y_vals, mode="lines+markers", line=dict(color="#10b981", width=3), name="Portfolio Capital (₹)")
    ])
    equity_fig.update_layout(
        paper_bgcolor="#202231",
        plot_bgcolor="#181924",
        font=dict(color="#ffffff"),
        margin=dict(l=40, r=20, t=20, b=30),
        xaxis=dict(showgrid=True, gridcolor="#2a2c3d"),
        yaxis=dict(showgrid=True, gridcolor="#2a2c3d")
    )

    # 2. VIX & PCR Graph
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT timestamp, underlying_price, vix, pcr FROM agent_debates ORDER BY timestamp DESC LIMIT 30")
        debates = [dict(row) for row in cursor.fetchall()]

    if debates:
        df_debates = pd.DataFrame(debates).sort_values("timestamp")
        vix_pcr_fig = go.Figure()
        vix_pcr_fig.add_trace(go.Scatter(x=df_debates["timestamp"], y=df_debates["vix"], mode="lines", name="India VIX", line=dict(color="#ef4444", width=2)))
        vix_pcr_fig.add_trace(go.Scatter(x=df_debates["timestamp"], y=df_debates["pcr"], mode="lines", name="PCR", line=dict(color="#f59e0b", width=2), yaxis="y2"))

        vix_pcr_fig.update_layout(
            paper_bgcolor="#202231",
            plot_bgcolor="#181924",
            font=dict(color="#ffffff"),
            margin=dict(l=40, r=40, t=20, b=30),
            xaxis=dict(showgrid=True, gridcolor="#2a2c3d"),
            yaxis=dict(title="India VIX", showgrid=True, gridcolor="#2a2c3d"),
            yaxis2=dict(title="PCR", overlaying="y", side="right", showgrid=False)
        )
    else:
        vix_pcr_fig = go.Figure()
        vix_pcr_fig.update_layout(
            paper_bgcolor="#202231",
            plot_bgcolor="#181924",
            font=dict(color="#ffffff"),
            margin=dict(l=40, r=40, t=20, b=30)
        )

    # 3. Trades DataTable
    if trades:
        df_trades_display = pd.DataFrame(trades)[["trade_id", "symbol", "action", "quantity", "entry_price", "pnl", "status"]]
        trades_table = dash_table.DataTable(
            data=df_trades_display.to_dict('records'),
            columns=[{"name": i.upper(), "id": i} for i in df_trades_display.columns],
            style_header={'backgroundColor': '#181924', 'color': '#00d2ff', 'fontWeight': 'bold'},
            style_cell={'backgroundColor': '#202231', 'color': '#ffffff', 'textAlign': 'center', 'border': '1px solid #2a2c3d', 'padding': '10px'}
        )
    else:
        trades_table = html.P("No trades executed yet.", style={"color": "#8a8d9b", "textAlign": "center", "padding": "20px"})

    # 4. Debates DataTable
    if debates:
        df_debates_display = pd.DataFrame(debates)[["timestamp", "underlying_price", "vix", "pcr"]]
        debates_table = dash_table.DataTable(
            data=df_debates_display.to_dict('records'),
            columns=[{"name": i.upper(), "id": i} for i in df_debates_display.columns],
            style_header={'backgroundColor': '#181924', 'color': '#00d2ff', 'fontWeight': 'bold'},
            style_cell={'backgroundColor': '#202231', 'color': '#ffffff', 'textAlign': 'center', 'border': '1px solid #2a2c3d', 'padding': '10px'}
        )
    else:
        debates_table = html.P("No agent debates logged yet.", style={"color": "#8a8d9b", "textAlign": "center", "padding": "20px"})

    return equity_fig, vix_pcr_fig, trades_table, debates_table

if __name__ == "__main__":
    app.run_server(debug=False, port=8050)
