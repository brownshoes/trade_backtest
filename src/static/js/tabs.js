const tabs = document.querySelectorAll('#tabs a');
const panes = document.querySelectorAll('.tab-pane');
let tradingViewInitialized = false;

// Helper function to show selected tab
function showTab(tabName) {
    tabs.forEach(t => t.classList.remove('active'));
    panes.forEach(p => p.style.display = 'none');

    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    document.getElementById(`${tabName}Tab`).style.display = 'block';

    // Initialize TradingView chart when chart tab is shown
    if (tabName === 'chart' && !tradingViewInitialized) {
        // Small delay to ensure DOM is ready
        setTimeout(() => {
            if (typeof initTradingViewChart === 'function') {
                initTradingViewChart();
                tradingViewInitialized = true;
            }
        }, 100);
    }
}

// Load saved tab or default to "load"
const savedTab = localStorage.getItem('activeTab') || 'load';
showTab(savedTab);

// Set up listeners
tabs.forEach(tab => {
    tab.addEventListener('click', e => {
        e.preventDefault();
        const target = tab.dataset.tab;
        showTab(target);
        localStorage.setItem('activeTab', target);
    });
});