import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import pandas as pd
from dashboard.data_provider import DashboardDataProvider

def create_dashboard_app(data_provider: DashboardDataProvider):
    app = dash.Dash(__name__, title="Nifty Multi-Agent Trading System")

    app.layout = html.Div(style={'backgroundColor': '#1e1e2f', 'color': '#ffffff', 'fontFamily': 'sans-serif', 'padding': '20px'}, children=[
        html.H1("Nifty Multi-Agent AI Options Trading System", style={'textAlign': 'center', 'color': '#00d2ff'}),

        # Header Status Bar
        html.Div(id='header-status', style={'display': 'flex', 'justifyContent': 'space-around', 'backgroundColor': '#27293d', 'padding': '15px', 'borderRadius': '8px', 'marginBottom': '20px'}, children=[
            html.Div([html.H4("Trading Mode", style={'margin': '0', 'color': '#a9a9a9'}), html.H2(id='mode-val', style={'margin': '5px 0', 'color': '#00e676'})]),
            html.Div([html.H4("Total Capital (₹)", style={'margin': '0', 'color': '#a9a9a9'}), html.H2(id='capital-val', style={'margin': '5px 0'})]),
            html.Div([html.H4("Net PnL (₹)", style={'margin': '0', 'color': '#a9a9a9'}), html.H2(id='pnl-val', style={'margin': '5px 0'})]),
            html.Div([html.H4("Active Positions", style={'margin': '0', 'color': '#a9a9a9'}), html.H2(id='positions-val', style={'margin': '5px 0'})]),
            html.Div([html.H4("Kill Switch Status", style={'margin': '0', 'color': '#a9a9a9'}), html.H2(id='killswitch-val', style={'margin': '5px 0'})]),
        ]),

        # Charts and Debate Section
        html.Div(style={'display': 'flex', 'gap': '20px'}, children=[
            html.Div(style={'flex': '1', 'backgroundColor': '#27293d', 'padding': '15px', 'borderRadius': '8px'}, children=[
                html.H3("Equity Curve", style={'color': '#00d2ff'}),
                dcc.Graph(id='equity-graph')
            ]),
            html.Div(style={'flex': '1', 'backgroundColor': '#27293d', 'padding': '15px', 'borderRadius': '8px'}, children=[
                html.H3("Latest Multi-Agent Debate Logs", style={'color': '#00d2ff'}),
                html.Div(id='debate-log-container', style={'height': '350px', 'overflowY': 'auto', 'fontFamily': 'monospace'})
            ])
        ]),

        dcc.Interval(id='interval-component', interval=2000, n_intervals=0)
    ])

    @app.callback(
        [Output('mode-val', 'children'), Output('capital-val', 'children'), Output('pnl-val', 'children'),
         Output('positions-val', 'children'), Output('killswitch-val', 'children'),
         Output('equity-graph', 'figure'), Output('debate-log-container', 'children')],
        [Input('interval-component', 'n_intervals')]
    )
    def update_dashboard(n):
        summary = data_provider.get_summary_metrics()

        mode = summary["trading_mode"]
        capital = f"₹{summary['total_capital']:,}"
        pnl = f"₹{summary['net_pnl']:,}"
        pnl_style = {'color': '#00e676'} if summary['net_pnl'] >= 0 else {'color': '#ff5252'}
        pos_count = str(summary["active_positions_count"])
        ks = "ACTIVE" if summary["kill_switch"] else "NORMAL"
        ks_style = {'color': '#ff5252'} if summary["kill_switch"] else {'color': '#00e676'}

        # Equity figure
        fig = go.Figure()
        fig.add_trace(go.Scatter(y=[100000.0, 100000.0 + summary['net_pnl']], mode='lines+markers', line=dict(color='#00d2ff', width=3)))
        fig.update_layout(template='plotly_dark', paper_bgcolor='#27293d', plot_bgcolor='#27293d', margin=dict(l=20, r=20, t=20, b=20))

        # Debate logs
        logs_html = []
        for log in data_provider.recent_debate_logs:
            decision = log.get("decision", "NO_TRADE")
            logs_html.append(html.Div(style={'borderBottom': '1px solid #3a3b5c', 'padding': '8px'}, children=[
                html.Span(f"[{log.get('llm_brain_decision', {}).get('market_regime', 'N/A')}] ", style={'color': '#f39c12'}),
                html.Span(f"Decision: {decision} ", style={'fontWeight': 'bold', 'color': '#00e676' if decision != 'NO_TRADE' else '#e74c3c'}),
                html.P(f"LLM Reasoning: {log.get('llm_brain_decision', {}).get('reasoning_summary', 'N/A')}", style={'margin': '2px 0', 'color': '#cccccc'})
            ]))

        return mode, capital, html.Span(pnl, style=pnl_style), pos_count, html.Span(ks, style=ks_style), fig, logs_html

    return app
