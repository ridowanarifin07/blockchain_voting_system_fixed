// Main JavaScript for SecureVote Application

// Utility Functions
function showAlert(message, type = 'success') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.innerHTML = `
        <span>${type === 'success' ? '✓' : type === 'error' ? '✗' : '⚠'}</span>
        <span>${message}</span>
    `;
    
    document.body.appendChild(alertDiv);
    
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString();
}

function formatHash(hash) {
    if (!hash) return '';
    return `${hash.substring(0, 8)}...${hash.substring(hash.length - 8)}`;
}

// Animation observers
document.addEventListener('DOMContentLoaded', () => {
    // Observe elements for animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }, observerOptions);
    
    document.querySelectorAll('.feature-card, .step, .candidate-card').forEach(el => {
        observer.observe(el);
    });
    
    // Smooth scroll for navigation links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
});

// API Helper Functions
async function apiRequest(endpoint, method = 'GET', data = null) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        }
    };
    
    if (data) {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(endpoint, options);
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.message || 'Request failed');
        }
        
        return result;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// Election Timer
function startElectionTimer(endTime) {
    const timerElement = document.getElementById('electionTimer');
    if (!timerElement) return;
    
    function updateTimer() {
        const now = new Date();
        const end = new Date(endTime);
        const diff = end - now;
        
        if (diff <= 0) {
            timerElement.textContent = 'Election Closed';
            return;
        }
        
        const hours = Math.floor(diff / (1000 * 60 * 60));
        const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((diff % (1000 * 60)) / 1000);
        
        timerElement.textContent = `Time Remaining: ${hours}h ${minutes}m ${seconds}s`;
    }
    
    updateTimer();
    setInterval(updateTimer, 1000);
}

// Live Results Updates
function startLiveResults() {
    async function updateResults() {
        try {
            const data = await apiRequest('/api/results');
            updateResultsDisplay(data);
        } catch (error) {
            console.error('Failed to update results:', error);
        }
    }
    
    updateResults();
    setInterval(updateResults, 10000); // Update every 10 seconds
}

function updateResultsDisplay(data) {
    const resultsContainer = document.getElementById('resultsContainer');
    if (!resultsContainer) return;
    
    // Update results visualization
    // This would be implemented with Chart.js or similar library
    console.log('Results updated:', data);
}

// Blockchain Explorer
async function loadBlockchain() {
    try {
        const data = await apiRequest('/api/blockchain');
        displayBlockchain(data);
    } catch (error) {
        showAlert('Failed to load blockchain data', 'error');
    }
}

function displayBlockchain(data) {
    const container = document.getElementById('blockchainContainer');
    if (!container) return;
    
    container.innerHTML = '';
    
    data.chain.forEach(block => {
        const blockElement = document.createElement('div');
        blockElement.className = 'blockchain-block';
        blockElement.innerHTML = `
            <div class="block-header">
                <h3>Block #${block.index}</h3>
                <span class="block-time">${formatDate(block.timestamp)}</span>
            </div>
            <div class="block-details">
                <div class="detail-row">
                    <span class="label">Hash:</span>
                    <span class="value">${formatHash(block.hash)}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Previous Hash:</span>
                    <span class="value">${formatHash(block.previous_hash)}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Votes:</span>
                    <span class="value">${block.votes_count}</span>
                </div>
            </div>
        `;
        container.appendChild(blockElement);
    });
}

// Analytics Charts
function initializeCharts() {
    // This would integrate with Chart.js or similar
    // Example: Voting trends over time, demographic breakdowns, etc.
    console.log('Charts initialized');
}

// Dark Mode Toggle
function toggleDarkMode() {
    document.body.classList.toggle('light-mode');
    const isDark = !document.body.classList.contains('light-mode');
    localStorage.setItem('darkMode', isDark ? 'true' : 'false');
}

// Initialize dark mode preference
if (localStorage.getItem('darkMode') === 'false') {
    document.body.classList.add('light-mode');
}

// Export functions for use in other scripts
window.SecureVote = {
    apiRequest,
    showAlert,
    formatDate,
    formatHash,
    startElectionTimer,
    startLiveResults,
    loadBlockchain,
    toggleDarkMode
};
