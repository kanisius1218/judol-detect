// Message Detection System - JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const messageInput = document.getElementById('messageInput');
    const detectBtn = document.getElementById('detectBtn');
    const clearBtn = document.getElementById('clearBtn');
    const resultArea = document.getElementById('resultArea');
    const resultLabel = document.getElementById('resultLabel');
    const confidenceFill = document.getElementById('confidenceFill');
    const confidenceText = document.getElementById('confidenceText');
    const timestamp = document.getElementById('timestamp');
    
    const batchInput = document.getElementById('batchInput');
    const batchBtn = document.getElementById('batchBtn');
    const batchResults = document.getElementById('batchResults');
    const batchResultsList = document.getElementById('batchResultsList');
    
    const totalChecks = document.getElementById('totalChecks');
    const spamCount = document.getElementById('spamCount');
    const hamCount = document.getElementById('hamCount');
    const spamRate = document.getElementById('spamRate');
    
    const historyList = document.getElementById('historyList');
    const clearHistoryBtn = document.getElementById('clearHistoryBtn');

    // Initialize
    loadStats();
    loadHistory();

    // Single Detection
    detectBtn.addEventListener('click', async function() {
        const text = messageInput.value.trim();
        
        if (!text) {
            alert('Please enter a message to analyze');
            return;
        }

        // Show loading
        detectBtn.disabled = true;
        detectBtn.querySelector('.btn-text').textContent = 'Analyzing...';
        detectBtn.querySelector('.loader').style.display = 'inline-block';

        try {
            const response = await fetch('/api/detect', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ text: text })
            });

            const data = await response.json();

            if (response.ok) {
                displayResult(data);
                loadStats();
                loadHistory();
            } else {
                alert('Error: ' + (data.error || 'Unknown error'));
            }
        } catch (error) {
            alert('Network error: ' + error.message);
        } finally {
            // Reset button
            detectBtn.disabled = false;
            detectBtn.querySelector('.btn-text').textContent = 'Analyze Message';
            detectBtn.querySelector('.loader').style.display = 'none';
        }
    });

    // Clear button
    clearBtn.addEventListener('click', function() {
        messageInput.value = '';
        resultArea.style.display = 'none';
    });

    // Display single result
    function displayResult(data) {
        resultArea.style.display = 'block';
        resultArea.classList.add('fade-in');
        
        // Set label
        resultLabel.textContent = data.label;
        resultLabel.className = 'label ' + data.label.toLowerCase();
        
        // Set confidence bar
        const confidencePercent = Math.round(data.confidence * 100);
        confidenceFill.style.width = confidencePercent + '%';
        confidenceText.textContent = confidencePercent + '%';
        
        // Set timestamp
        const date = new Date(data.timestamp);
        timestamp.textContent = date.toLocaleString();
    }

    // Batch Processing
    batchBtn.addEventListener('click', async function() {
        const texts = batchInput.value.trim().split('\n').filter(t => t.trim());
        
        if (texts.length === 0) {
            alert('Please enter at least one message');
            return;
        }

        // Show loading
        batchBtn.disabled = true;
        batchBtn.textContent = 'Processing...';

        try {
            const response = await fetch('/api/batch', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ texts: texts })
            });

            const data = await response.json();

            if (response.ok) {
                displayBatchResults(data.results);
                loadStats();
                loadHistory();
            } else {
                alert('Error: ' + (data.error || 'Unknown error'));
            }
        } catch (error) {
            alert('Network error: ' + error.message);
        } finally {
            batchBtn.disabled = false;
            batchBtn.textContent = 'Process Batch';
        }
    });

    // Display batch results
    function displayBatchResults(results) {
        batchResults.style.display = 'block';
        batchResultsList.innerHTML = '';

        results.forEach(result => {
            const item = document.createElement('div');
            item.className = 'batch-result-item fade-in';
            
            const confidencePercent = Math.round(result.confidence * 100);
            
            item.innerHTML = `
                <div class="batch-result-text">${escapeHtml(result.text)}</div>
                <div class="batch-result-label ${result.label.toLowerCase()}">
                    ${result.label} (${confidencePercent}%)
                </div>
            `;
            
            batchResultsList.appendChild(item);
        });
    }

    // Load statistics
    async function loadStats() {
        try {
            const response = await fetch('/api/stats');
            const data = await response.json();

            if (response.ok) {
                totalChecks.textContent = data.total_checks;
                spamCount.textContent = data.spam_count;
                hamCount.textContent = data.ham_count;
                spamRate.textContent = data.spam_rate + '%';
            }
        } catch (error) {
            console.error('Error loading stats:', error);
        }
    }

    // Load history
    async function loadHistory() {
        try {
            const response = await fetch('/api/history');
            const data = await response.json();

            if (response.ok) {
                displayHistory(data.history);
            }
        } catch (error) {
            console.error('Error loading history:', error);
        }
    }

    // Display history
    function displayHistory(history) {
        if (history.length === 0) {
            historyList.innerHTML = '<p class="empty-state">No detection history yet</p>';
            return;
        }

        historyList.innerHTML = '';
        
        // Show recent items first
        history.reverse().forEach(item => {
            const historyItem = document.createElement('div');
            historyItem.className = 'history-item fade-in';
            
            const confidencePercent = Math.round(item.confidence * 100);
            const date = new Date(item.timestamp);
            
            historyItem.innerHTML = `
                <div class="history-text">${escapeHtml(item.text)}</div>
                <div class="history-meta">
                    <span class="history-label ${item.result.toLowerCase()}">${item.result}</span>
                    <span class="history-confidence">${confidencePercent}%</span>
                </div>
            `;
            
            historyList.appendChild(historyItem);
        });
    }

    // Clear history
    clearHistoryBtn.addEventListener('click', async function() {
        if (!confirm('Are you sure you want to clear the history?')) {
            return;
        }

        try {
            const response = await fetch('/api/clear-history', {
                method: 'POST'
            });

            if (response.ok) {
                loadHistory();
                loadStats();
            }
        } catch (error) {
            alert('Error clearing history: ' + error.message);
        }
    });

    // Utility function to escape HTML
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Auto-refresh stats every 30 seconds
    setInterval(function() {
        loadStats();
    }, 30000);

    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + Enter to analyze
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            if (messageInput.value.trim()) {
                detectBtn.click();
            }
        }
        
        // Escape to clear
        if (e.key === 'Escape') {
            clearBtn.click();
        }
    });

    // Add smooth scrolling
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

    // Add input character counter
    messageInput.addEventListener('input', function() {
        const charCount = this.value.length;
        if (!document.getElementById('charCounter')) {
            const counter = document.createElement('div');
            counter.id = 'charCounter';
            counter.style.cssText = 'text-align: right; color: #6c757d; font-size: 0.85rem; margin-top: 5px;';
            this.parentElement.insertBefore(counter, this.nextSibling);
        }
        document.getElementById('charCounter').textContent = `${charCount} characters`;
    });

    // Add copy result functionality
    resultArea.addEventListener('click', function(e) {
        if (e.target.classList.contains('label')) {
            const text = `Result: ${resultLabel.textContent} (${confidenceText.textContent})`;
            navigator.clipboard.writeText(text).then(() => {
                const originalText = resultLabel.textContent;
                resultLabel.textContent = 'Copied!';
                setTimeout(() => {
                    resultLabel.textContent = originalText;
                }, 1000);
            });
        }
    });
});
