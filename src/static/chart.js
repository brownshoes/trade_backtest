fetch("/ohlc")
  .then(response => response.json())
  .then(({ ohlc, sma }) => {
    console.log("Data loaded:", ohlc.length, "candles, and", sma.length, "SMA points");

    const chart = LightweightCharts.createChart(document.getElementById("chart"), {
      width: 800,
      height: 400,
      layout: { background: { color: '#fff' }, textColor: '#000' },
      grid: {
        vertLines: { color: '#e0e0e0' },
        horzLines: { color: '#e0e0e0' },
      },
      timeScale: {
        timeVisible: true,
        secondsVisible: true,
      },
    });

    // OHLC Candlestick
    const candleSeries = chart.addCandlestickSeries({
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderVisible: false,
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350',
    });
    candleSeries.setData(ohlc);

    // SMA Line
    const smaSeries = chart.addLineSeries({
      color: '#f39c12',
      lineWidth: 2,
    });
    smaSeries.setData(sma);

    chart.timeScale().fitContent();
  })
  .catch(err => {
    console.error("Error loading chart data:", err);
  });
