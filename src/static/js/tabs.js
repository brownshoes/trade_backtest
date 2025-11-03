document.querySelectorAll('#tabs a').forEach(tab => {
    tab.addEventListener('click', (e) => {
        e.preventDefault();
        const target = tab.dataset.tab;

        // Remove active class from all tabs
        document.querySelectorAll('#tabs a').forEach(t => t.classList.remove('active'));

        // Hide all tab panes
        document.querySelectorAll('.tab-pane').forEach(pane => pane.style.display = 'none');

        // Show the selected tab
        document.getElementById(target + 'Tab').style.display = 'block';
        tab.classList.add('active');
    });
});

const savedTab = localStorage.getItem('activeTab') || 'load';
document.querySelector(`[data-tab="${savedTab}"]`).click();

document.querySelectorAll('#tabs a').forEach(tab => {
    tab.addEventListener('click', () => {
        localStorage.setItem('activeTab', tab.dataset.tab);
    });
});
