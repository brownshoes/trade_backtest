from flask import Flask, render_template, jsonify
import csv

from init.initalization import flask_init
from init.flask_init import default_startup, container, flask_backtest, DEFAULT_CONFIG

from core.position_tracking.statistics import Statistics

import plotly.express as px
import pandas as pd
import plotly.graph_objects as go

from database.db_setup import init_db



from log.logger import setup_logger
#from log.logger import setup_logger
log = setup_logger("Flask", mode="off")

init_db()

default_startup()

app = Flask(__name__)



import pandas as pd
import plotly.graph_objs as go
from flask import Flask, render_template
import plotly.offline as pyo

app = Flask(__name__)

@app.route('/test2')
def test2():
    config = flask_backtest(DEFAULT_CONFIG, container.curr_df)
    trading_state = config.trading_state
    closed_positions = [cp.to_dict() for cp in trading_state.closed_positions]
    statistics = Statistics(trading_state, config.main_time_series.candle_size)
    metrics = statistics.to_dict()

    df = pd.DataFrame(closed_positions)
    df['close_datetime'] = pd.to_datetime(df['close_datetime'])
    df.sort_values('close_datetime', inplace=True)
    df.reset_index(drop=True, inplace=True)

    # Use trade index as x-axis
    df['trade_index'] = df.index

    # Colors for profit and loss bars
    bar_colors = ['green' if pnl >= 0 else 'red' for pnl in df['profit_and_loss']]

    pnl_bars = go.Bar(
        x=df['trade_index'],
        y=df['profit_and_loss'],
        marker_color=bar_colors,
        name='P&L',
        width=0.98
    )

    runup_bars = go.Bar(
        x=df['trade_index'],
        y=df['run_up'],
        marker_color='lightgreen',
        name='Run-up',
        opacity=0.4
    )

    drawdown_bars = go.Bar(
        x=df['trade_index'],
        y=df['drawdown'],
        marker_color='lightcoral',
        name='Drawdown',
        opacity=0.4
    )

    equity_line = go.Scatter(
        x=df['trade_index'],
        y=df['cumulative_profit_and_loss'],
        mode='lines+markers',
        name='Equity Curve',
        line=dict(color='darkred')
    )

    # Create timeline labels for secondary x-axis (dates formatted)
    timeline_labels = df['close_datetime'].dt.strftime('%Y-%m-%d').tolist()

    chart_width = max(1400, len(df) * 50)

    layout = go.Layout(
        title='Trading Strategy Performance',
        barmode='overlay',
        bargap=0.0,       # no gaps between groups
        bargroupgap=0.0,  # no gaps inside groups
        width=chart_width,
        height=700,
        xaxis=dict(
            title='Trade Number',
            tickmode='array',
            tickvals=df['trade_index'],
            ticktext=[str(i+1) for i in df['trade_index']],  # Show trade # starting at 1
            showgrid=False,
        ),
        xaxis2=dict(
            title='Trade Close Date',
            overlaying='x',
            side='bottom',
            tickmode='array',
            tickvals=df['trade_index'],
            ticktext=timeline_labels,
            tickangle=45,
            showgrid=False,
            showline=True,
            linewidth=1,
            linecolor='black',
            ticks='outside',
            ticklen=8,
        ),
        yaxis=dict(
            title='Profit / Amount',
        ),
        legend=dict(orientation='h'),
        template='plotly_white',
        margin=dict(b=100)  # Extra bottom margin for date labels
    )

    data = [runup_bars, drawdown_bars, pnl_bars, equity_line]
    fig = go.Figure(data=data, layout=layout)

    plot_html = pyo.plot(fig, output_type='div')
    
    PIXELS_PER_TRADE = 50
    MAX_VISIBLE_TRADES = 100
    chart_width = len(df) * PIXELS_PER_TRADE
    visible_window_width = MAX_VISIBLE_TRADES * PIXELS_PER_TRADE
    enable_scroll = len(df) > MAX_VISIBLE_TRADES


    #return render_template('test2.html', plot_html=plot_html)
    return render_template('test2.html', plot_html=plot_html, metrics=metrics, positions=closed_positions, enable_scroll=enable_scroll, visible_window_width=visible_window_width)


@app.route('/test')
def test():
    # # Placeholder data for your chart (you will replace this with your actual data)
    # data = {
    #     'date': pd.date_range(start='2025-04-30', periods=61, freq='D'),
    #     'profit': [50, -30, 40, -60, 20, 90, -20, -50, 30, 10, 50, -70, -20, 10, 80, 40, 10, -60, 90, -10, 40, 10, 20, 10, -80, 50, -10, -30, 50, 20, -40, 30, 10, 50, -20, -30, 10, -20, 60, 20, -50, 30, -70, 40, 20, -20, 30, 10, -50, 40, -20, -40, 50, 10, -20, 30, -50, -10, 20, 10, 15],
    #     'cumulative_profit': [50, 20, 60, 0, 20, 110, 90, 40, 70, 80, 130, 60, 40, 50, 130, 170, 180, 120, 210, 200, 240, 250, 270, 280, 200, 250, 240, 210, 260, 280, 240, 270, 260, 300, 280, 250, 260, 240, 300, 320, 270, 300, 230, 270, 290, 270, 300, 310, 260, 300, 260, 230, 280, 290, 270, 300, 250, 240, 260, 270, 280]
    # }

    
    # Original 61 profit values
    base_profits = [
        50, -30, 40, -60, 20, 90, -20, -50, 30, 10,
        50, -70, -20, 10, 80, 40, 10, -60, 90, -10,
        40, 10, 20, 10, -80, 50, -10, -30, 50, 20,
        -40, 30, 10, 50, -20, -30, 10, -20, 60, 20,
        -50, 30, -70, 40, 20, -20, 30, 10, -50, 40,
        -20, -40, 50, 10, -20, 30, -50, -10, 20, 10, 15
    ]

    # Repeat pattern to get 300 values
    profit = base_profits * 4 + base_profits[:56]  # 61*4 + 56 = 300

    # Calculate cumulative profit
    cumulative_profit = pd.Series(profit).cumsum().tolist()

    # Create DataFrame
    data = pd.DataFrame({
        'date': pd.date_range(start='2025-04-30', periods=300, freq='D'),
        'profit': profit,
        'cumulative_profit': cumulative_profit
    })

    #    Check the lengths of the lists
    print(len(data['date']), len(data['profit']), len(data['cumulative_profit']))

    data = pd.DataFrame({
        'date': pd.date_range(start='2025-04-30', periods=300, freq='D'),
        'profit': profit,
        'cumulative_profit': cumulative_profit
    })

    df = pd.DataFrame(data)

    # Create the figure
    fig = go.Figure()

    # Add the cumulative profit line
    fig.add_trace(go.Scatter(x=df['date'], y=df['cumulative_profit'], mode='lines', name='Cumulative Profit', line=dict(color='blue')))

    # Add the profit bars, setting color based on whether profit is positive or negative
    fig.add_trace(go.Bar(
        x=df['date'],
        y=df['profit'],
        name='Profit',
        marker=dict(color=['green' if p > 0 else 'red' for p in df['profit']]),
    ))

    # Update layout: Remove dark theme and set title and labels
    fig.update_layout(
        title='Profit Over Time',
        xaxis_title='Date',
        yaxis_title='Profit',
        template='plotly',
        showlegend=True
    )

    # Convert plot to HTML
    graph_html = fig.to_html(full_html=False)

    return render_template('test.html', graph_html=graph_html)


def calculate_sma(data, period=5):
    sma = []
    closes = [row['close'] for row in data]
    for i in range(len(closes)):
        if i < period - 1:
            sma.append(None)
        else:
            avg = sum(closes[i - period + 1:i + 1]) / period
            sma.append(round(avg, 2))
    return sma

def load_data():
    ohlc_data = []
    with open("csv\\csv_backtest\\short_btc.csv", newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            ohlc_data.append({
                "time": int(float(row["Timestamp"])),  # UNIX timestamp (seconds)
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
            })

    sma_values = calculate_sma(ohlc_data, period=5)

    sma_data = [
        {"time": row["time"], "value": sma}
        for row, sma in zip(ohlc_data, sma_values)
        if sma is not None  # Remove initial nulls for chart clarity
    ]

    return {
        "ohlc": ohlc_data,
        "sma": sma_data
    }

@app.route('/report')
def closed_position_view_report():
    config = flask_backtest(DEFAULT_CONFIG, container.curr_df)
    trading_state = config.trading_state
    closed_positions = [
        cp.to_dict() for cp in trading_state.closed_positions
    ]
    statistics = Statistics(trading_state, config.main_time_series.candle_size)
    metrics = statistics.to_dict()
    return render_template('report.html', positions=closed_positions, metrics=metrics)

@app.route('/closed-position')
def closed_position_view():
    config = flask_backtest(DEFAULT_CONFIG, container.curr_df)
    trading_state = config.trading_state
    closed_positions = [
        cp.to_dict() for cp in trading_state.closed_positions
    ]
    return render_template('closed_position.html', positions=closed_positions)


@app.route("/")
def index():
    return render_template("index.html")

# @app.route("/ohlc")
# def ohlc():
#     return jsonify(load_data())



if __name__ == "__main__":
    app.run(debug=True)
