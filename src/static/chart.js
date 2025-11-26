<div id="tvChartContainer" style="width:100%; height:500px;"></div>

<script>
let chart;
let candleSeries;

function createChart() {
    const container = document.getElementById('tvChartContainer');

    // Create the chart using LightweightCharts
    chart = LightweightCharts.createChart(container, {
        width: container.clientWidth,
        height: 500,
        layout: {
            background: { color: '#ffffff' },
            textColor: '#222',
        },
        grid: {
            vertLines: { color: '#eee' },
            horzLines: { color: '#eee' },
        }
    });

    // ✅ UPDATED: Use addSeries and specify the type
    candleSeries = chart.addSeries({ type: 'Candlestick' });

    // Example demo data
    const data = [
        { time: '2024-01-01', open: 100, high: 105, low: 98, close: 102 },
        { time: '2024-01-02', open: 102, high: 108, low: 101, close: 107 },
        { time: '2024-01-03', open: 107, high: 110, low: 103, close: 104 },
        { time: '2024-01-04', open: 104, high: 106, low: 99, close: 100 },
    ];

    candleSeries.setData(data);
}

// Create chart once
createChart();

// Resize when chart tab becomes visible
document.addEventListener("chartTabVisible", () => {
    const container = document.getElementById("tvChartContainer");
    chart.applyOptions({ width: container.clientWidth });
    chart.timeScale().fitContent();
});
</script>
