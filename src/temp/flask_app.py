from flask import Flask, render_template
import plotly.graph_objs as go
import pandas as pd
from datetime import datetime

from factories.initalization import init, load_config, load_csv

import logging
from log.logger import LOGGER_NAME
logger = logging.getLogger(LOGGER_NAME)

app = Flask(__name__)

@app.route('/')
def index():
    init("configs.test")
    config = load_config("configs.test")
    config_output = config.to_string()

    logger.info(config_output)

    df, list_of_dict = load_csv(config)

    # Create candlestick chart
    fig = go.Figure(data=[go.Candlestick(
        x=df['Datetime'],
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close']
    )])

    fig.update_layout(title='Sample Candlestick Chart', xaxis_title='Date', yaxis_title='Price')

    # Convert Plotly chart to HTML
    graph_html = fig.to_html(full_html=False)

    return render_template('index.html', graph_html=graph_html)

if __name__ == '__main__':
    app.run(debug=True)
