
// Initialize dashboard
loadFinancialSummary();
loadRecentExpenses();
loadRecentIncomes();
loadUpcomingEvents();  // Add this
loadUpcomingTasks();   // Add this
loadSavingsGoals();

// Refresh data every 5 minutes
setInterval(() => {
    loadFinancialSummary();
    loadRecentExpenses();
    loadRecentIncomes();
    loadUpcomingEvents();  // Add this
    loadUpcomingTasks();   // Add this
    loadSavingsGoals();
}, 300000);

// Global utility functions
document.addEventListener('DOMContentLoaded', function() {
    // Set default dates in forms
    setDefaultDates();
    
    // Initialize tooltips
    initTooltips();
});

function setDefaultDates() {
    const today = new Date().toISOString().split('T')[0];
    const now = new Date();
    const timeNow = now.toTimeString().substring(0, 5);
    
    // Set default date values in forms
    const dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(input => {
        if (!input.value && input.id !== 'event-end-date') {
            input.value = today;
        }
    });
    
    // Set default time values
    const timeInputs = document.querySelectorAll('input[type="time"]');
    timeInputs.forEach(input => {
        if (!input.value) {
            input.value = timeNow;
        }
    });
}

function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Currency formatting function
function formatCurrency(amount, currency = 'Tsh') {
    return currency + parseFloat(amount).toFixed(2);
}

// Date formatting function
function formatDate(dateString) {
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return new Date(dateString).toLocaleDateString(undefined, options);
}

// API error handling
function handleApiError(error) {
    console.error('API Error:', error);
    Swal.fire({
        icon: 'error',
        title: 'Error',
        text: 'An error occurred while processing your request. Please try again.'
    });
}