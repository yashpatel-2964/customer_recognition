// Main JavaScript file for Customer Recognition System

// DOM elements and initialization
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Setup edit bill form toggle
    setupEditBillForm();
    
    // Setup auto refresh
    setupAutoRefresh();
    
    // Setup chart if on history page
    if (document.getElementById('purchaseHistoryChart')) {
        setupHistoryChart();
    }
});

// Function to toggle the edit bill form
function setupEditBillForm() {
    const editButton = document.getElementById('edit-bill-btn');
    const editForm = document.getElementById('edit-form');
    
    if (editButton && editForm) {
        editButton.addEventListener('click', function() {
            if (editForm.style.display === 'block') {
                editForm.style.display = 'none';
                editButton.textContent = 'Edit Amount';
            } else {
                editForm.style.display = 'block';
                editButton.textContent = 'Cancel';
            }
        });
    }
}

// Function to handle auto-refresh countdown
function setupAutoRefresh() {
    const countdownEl = document.getElementById('countdown');
    
    if (countdownEl) {
        let countdown = parseInt(countdownEl.textContent);
        
        setInterval(function() {
            countdown--;
            countdownEl.textContent = countdown;
            
            if (countdown <= 0) {
                location.reload();
            }
        }, 1000);
    }
}

// Function to set up history chart
function setupHistoryChart() {
    // Check if Chart.js is available
    if (typeof Chart === 'undefined') {
        console.error('Chart.js not loaded');
        return;
    }
    
    const ctx = document.getElementById('purchaseHistoryChart').getContext('2d');
    
    // Get data from the page
    const chartData = JSON.parse(document.getElementById('chart-data').textContent);
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: chartData.labels,
            datasets: [{
                label: 'Purchase Amount ($)',
                data: chartData.amounts,
                fill: false,
                borderColor: '#4e73df',
                tension: 0.1,
                pointBackgroundColor: '#4e73df',
                pointBorderColor: '#fff',
                pointRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: false,
                    title: {
                        display: true,
                        text: 'Amount ($)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Purchase Date'
                    }
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                }
            }
        }
    });
}

// Function to validate form inputs
function validateBillForm(formId) {
    const form = document.getElementById(formId);
    
    if (!form) return true;
    
    const amountInput = form.querySelector('input[name="actual_bill"]');
    
    if (amountInput && amountInput.value.trim() === '') {
        alert('Please enter a valid bill amount');
        return false;
    }
    
    if (amountInput && parseFloat(amountInput.value) < 0) {
        alert('Bill amount cannot be negative');
        return false;
    }
    
    return true;
}

// Function to handle manual customer lookup
function lookupCustomer() {
    const customerId = document.getElementById('customer-id-input').value.trim();
    
    if (customerId === '') {
        alert('Please enter a customer ID');
        return false;
    }
    
    return true;
}

// Function to confirm deletion (if needed)
function confirmDelete(customerId) {
    return confirm(`Are you sure you want to delete customer ${customerId}?`);
}