// FinSplit Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Add fade-in animation to cards
    var cards = document.querySelectorAll('.card');
    cards.forEach(function(card, index) {
        card.style.animationDelay = (index * 0.1) + 's';
        card.classList.add('fade-in');
    });
});

// UPI ID Validation
function validateUPI(upiId) {
    const upiRegex = /^[\w\.-]+@[\w\.-]+$/;
    return upiRegex.test(upiId);
}

// Real-time UPI validation
document.addEventListener('input', function(e) {
    if (e.target.name === 'upi_id' || e.target.id === 'id_upi_id') {
        const upiId = e.target.value;
        const feedback = e.target.parentNode.nextElementSibling;
        
        if (upiId && !validateUPI(upiId)) {
            e.target.classList.add('is-invalid');
            if (feedback && feedback.classList.contains('invalid-feedback')) {
                feedback.textContent = 'Please enter a valid UPI ID (e.g., user@paytm)';
            }
        } else {
            e.target.classList.remove('is-invalid');
            e.target.classList.add('is-valid');
        }
    }
});

// Expense Split Calculator
function calculateEqualSplit(totalAmount, memberCount) {
    const splitAmount = (totalAmount / memberCount).toFixed(2);
    return splitAmount;
}

function calculatePercentageSplit(totalAmount, percentage) {
    const splitAmount = (totalAmount * percentage / 100).toFixed(2);
    return splitAmount;
}

// Format currency display
function formatCurrency(amount) {
    return '₹' + parseFloat(amount).toFixed(2);
}

// Update currency displays
document.addEventListener('DOMContentLoaded', function() {
    const currencyElements = document.querySelectorAll('.currency');
    currencyElements.forEach(function(element) {
        const amount = element.textContent.replace(/[^\d.-]/g, '');
        if (amount) {
            element.textContent = formatCurrency(amount);
            element.classList.add('text-currency');
        }
    });
});

// Pool Search Functionality
function searchPools() {
    const searchInput = document.getElementById('poolSearch');
    const searchTerm = searchInput.value.toLowerCase();
    const poolCards = document.querySelectorAll('.pool-card');
    
    poolCards.forEach(function(card) {
        const poolName = card.querySelector('.card-title').textContent.toLowerCase();
        const poolDescription = card.querySelector('.card-text').textContent.toLowerCase();
        
        if (poolName.includes(searchTerm) || poolDescription.includes(searchTerm)) {
            card.style.display = 'block';
            card.classList.add('fade-in');
        } else {
            card.style.display = 'none';
        }
    });
}

// Add Expense Modal
function showAddExpenseModal() {
    // This would be implemented when we have the modal in templates
    console.log('Add expense modal would open here');
}

// Confirm Delete Actions
function confirmDelete(itemName, itemType) {
    return confirm(`Are you sure you want to delete this ${itemType}: "${itemName}"? This action cannot be undone.`);
}

// Settlement Calculator
function calculateOptimalSettlements(balances) {
    const creditors = [];
    const debtors = [];
    const settlements = [];
    
    // Separate creditors and debtors
    for (const [userId, balance] of Object.entries(balances)) {
        if (balance.balance > 0) {
            creditors.push({userId, amount: balance.balance, user: balance.user});
        } else if (balance.balance < 0) {
            debtors.push({userId, amount: Math.abs(balance.balance), user: balance.user});
        }
    }
    
    // Calculate settlements
    let i = 0, j = 0;
    while (i < creditors.length && j < debtors.length) {
        const credit = creditors[i];
        const debt = debtors[j];
        const settlementAmount = Math.min(credit.amount, debt.amount);
        
        settlements.push({
            from: debt.user,
            to: credit.user,
            amount: settlementAmount
        });
        
        credit.amount -= settlementAmount;
        debt.amount -= settlementAmount;
        
        if (credit.amount === 0) i++;
        if (debt.amount === 0) j++;
    }
    
    return settlements;
}

// Copy UPI ID to clipboard
function copyUPIId(upiId) {
    navigator.clipboard.writeText(upiId).then(function() {
        // Show success message
        const toast = document.createElement('div');
        toast.className = 'toast align-items-center text-white bg-success border-0';
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    UPI ID copied to clipboard!
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        document.body.appendChild(toast);
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        // Remove toast after it's hidden
        toast.addEventListener('hidden.bs.toast', function() {
            document.body.removeChild(toast);
        });
    });
}

// Form Validation
function validateForm(formId) {
    const form = document.getElementById(formId);
    const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
    let isValid = true;
    
    inputs.forEach(function(input) {
        if (!input.value.trim()) {
            input.classList.add('is-invalid');
            isValid = false;
        } else {
            input.classList.remove('is-invalid');
            input.classList.add('is-valid');
        }
    });
    
    return isValid;
}

// Loading States
function showLoading(buttonElement) {
    const originalText = buttonElement.textContent;
    buttonElement.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Loading...';
    buttonElement.disabled = true;
    
    return function hideLoading() {
        buttonElement.innerHTML = originalText;
        buttonElement.disabled = false;
    };
}

// API Helper Functions
async function apiCall(url, method = 'GET', data = null) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        }
    };
    
    if (data) {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(url, options);
        return await response.json();
    } catch (error) {
        console.error('API call failed:', error);
        throw error;
    }
}

// Get CSRF token from cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Responsive table helper
function makeTablesResponsive() {
    const tables = document.querySelectorAll('table');
    tables.forEach(function(table) {
        if (!table.parentNode.classList.contains('table-responsive')) {
            const wrapper = document.createElement('div');
            wrapper.className = 'table-responsive';
            table.parentNode.insertBefore(wrapper, table);
            wrapper.appendChild(table);
        }
    });
}

// Initialize responsive tables on page load
document.addEventListener('DOMContentLoaded', makeTablesResponsive);

