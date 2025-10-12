// Advanced Message Detection System - JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Tab Navigation
    const tabs = document.querySelectorAll('.nav-tab');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const targetTab = tab.getAttribute('data-tab');
            
            // Update active tab
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            // Show corresponding content
            tabContents.forEach(content => {
                content.classList.remove('active');
                if (content.id === `${targetTab}-tab`) {
                    content.classList.add('active');
                }
            });
        });
    });

    // Message Detection
    const messageInput = document.getElementById('messageInput');
    const detectBtn = document.getElementById('detectBtn');
    const clearBtn = document.getElementById('clearBtn');
    const charCount = document.getElementById('charCount');
    const resultCard = document.getElementById('resultCard');
    const deleteSpamBtn = document.getElementById('deleteSpamBtn');
    
    // Character counter
    messageInput?.addEventListener('input', function() {
        if (charCount) {
            charCount.textContent = `${this.value.length} characters`;
        }
    });

    // Detect message
    detectBtn?.addEventListener('click', async function() {
        const text = messageInput.value.trim();
        
        if (!text) {
            alert('Please enter a message to analyze');
            return;
        }

        detectBtn.disabled = true;
        detectBtn.textContent = 'Analyzing...';

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
                displayDetectionResult(data);
                updateStatistics();
            } else {
                alert('Error: ' + (data.error || 'Unknown error'));
            }
        } catch (error) {
            alert('Network error: ' + error.message);
        } finally {
            detectBtn.disabled = false;
            detectBtn.textContent = 'Analyze Message';
        }
    });

    // Clear input
    clearBtn?.addEventListener('click', function() {
        messageInput.value = '';
        charCount.textContent = '0 characters';
        resultCard.style.display = 'none';
    });

    // Display detection result
    function displayDetectionResult(data) {
        resultCard.style.display = 'block';
        
        const categoryLabel = document.getElementById('categoryLabel');
        const confidenceScore = document.getElementById('confidenceScore');
        const characteristicsList = document.getElementById('characteristicsList');
        
        // Set category
        categoryLabel.textContent = data.category.replace('_', ' ').toUpperCase();
        categoryLabel.className = data.category;
        
        // Set confidence
        const confidence = Math.round(data.confidence * 100);
        confidenceScore.textContent = `${confidence}% Confidence`;
        
        // Display characteristics
        characteristicsList.innerHTML = '';
        if (data.characteristics) {
            const chars = data.characteristics;
            
            // Add characteristics
            const items = [
                `Message length: ${chars.length} characters`,
                `Word count: ${chars.word_count}`,
                `URLs found: ${chars.url_count}`,
                `Numbers found: ${chars.number_count}`,
                `Uppercase ratio: ${(chars.uppercase_ratio * 100).toFixed(1)}%`,
                `Special characters: ${(chars.special_chars * 100).toFixed(1)}%`
            ];
            
            if (chars.category_keywords && chars.category_keywords.length > 0) {
                items.push(`Keywords detected: ${chars.category_keywords.join(', ')}`);
            }
            
            items.forEach(item => {
                const li = document.createElement('li');
                li.textContent = item;
                characteristicsList.appendChild(li);
            });
        }
        
        // Show delete button for spam/judi
        if (deleteSpamBtn) {
            if (data.category === 'spam' || data.category === 'judi_online') {
                deleteSpamBtn.style.display = 'inline-flex';
            } else {
                deleteSpamBtn.style.display = 'none';
            }
        }
    }

    // Delete spam messages
    deleteSpamBtn?.addEventListener('click', async function() {
        if (!confirm('Delete all detected spam and judi messages?')) {
            return;
        }

        try {
            const response = await fetch('/api/delete-spam', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ category: 'spam' })
            });

            const data = await response.json();

            if (response.ok) {
                alert(data.message);
                updateUserStats();
            } else {
                alert('Error: ' + (data.error || 'Unknown error'));
            }
        } catch (error) {
            alert('Network error: ' + error.message);
        }
    });

    // Social Media Analysis
    const socialUrl = document.getElementById('socialUrl');
    const analyzeUrlBtn = document.getElementById('analyzeUrlBtn');
    const urlAnalysisResult = document.getElementById('urlAnalysisResult');

    analyzeUrlBtn?.addEventListener('click', async function() {
        const url = socialUrl.value.trim();
        
        if (!url) {
            alert('Please enter a social media URL');
            return;
        }

        analyzeUrlBtn.disabled = true;
        analyzeUrlBtn.textContent = 'Analyzing...';

        try {
            const response = await fetch('/api/analyze-url', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ url: url })
            });

            const data = await response.json();

            if (response.ok) {
                displayUrlAnalysis(data);
            } else {
                alert('Error: ' + (data.error || 'Unknown error'));
            }
        } catch (error) {
            alert('Network error: ' + error.message);
        } finally {
            analyzeUrlBtn.disabled = false;
            analyzeUrlBtn.textContent = 'Analyze Comments';
        }
    });

    // Display URL analysis results
    function displayUrlAnalysis(data) {
        urlAnalysisResult.style.display = 'block';
        
        // Platform info
        document.getElementById('platformName').textContent = data.platform.toUpperCase();
        document.getElementById('analysisDate').textContent = new Date(data.analysis_date).toLocaleString();
        
        // Statistics
        document.getElementById('totalComments').textContent = data.total_comments;
        document.getElementById('spamComments').textContent = data.spam_comments;
        document.getElementById('judiComments').textContent = data.judi_comments;
        document.getElementById('spamPercentage').textContent = data.spam_percentage + '%';
        
        // Sample comments
        const sampleCommentsList = document.getElementById('sampleCommentsList');
        sampleCommentsList.innerHTML = '';
        
        if (data.sample_results) {
            data.sample_results.forEach(comment => {
                const div = document.createElement('div');
                div.className = 'comment-item';
                div.innerHTML = `
                    <span class="comment-text">${comment.text}</span>
                    <span class="comment-category ${comment.category}">${comment.category.replace('_', ' ')}</span>
                `;
                sampleCommentsList.appendChild(div);
            });
        }
        
        // Top spammers
        const topSpammersList = document.getElementById('topSpammersList');
        topSpammersList.innerHTML = '';
        
        if (data.top_spam_accounts) {
            Object.entries(data.top_spam_accounts).forEach(([username, count]) => {
                const div = document.createElement('div');
                div.className = 'spammer-row';
                div.innerHTML = `
                    <span>${data.platform}</span>
                    <span>${username}</span>
                    <span>${count} spam</span>
                    <button class="btn btn-small" onclick="researchAccount('${data.platform}', '${username}')">Research</button>
                `;
                topSpammersList.appendChild(div);
            });
        }
    }

    // Account Research
    const platformSelect = document.getElementById('platformSelect');
    const usernameInput = document.getElementById('usernameInput');
    const researchBtn = document.getElementById('researchBtn');
    const researchResult = document.getElementById('researchResult');

    researchBtn?.addEventListener('click', async function() {
        const platform = platformSelect.value;
        const username = usernameInput.value.trim();
        
        if (!platform || !username) {
            alert('Please select platform and enter username');
            return;
        }

        await researchAccount(platform, username);
    });

    // Research account function
    window.researchAccount = async function(platform, username) {
        try {
            const response = await fetch('/api/research-account', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ platform, username })
            });

            const data = await response.json();

            if (response.ok) {
                displayResearchResult(data);
                
                // Switch to research tab
                document.querySelector('[data-tab="research"]').click();
            } else {
                alert('Error: ' + (data.error || 'Unknown error'));
            }
        } catch (error) {
            alert('Network error: ' + error.message);
        }
    };

    // Display research results
    function displayResearchResult(data) {
        researchResult.style.display = 'block';
        
        // Account info
        document.getElementById('accountPlatform').textContent = data.platform.toUpperCase();
        document.getElementById('accountUsername').textContent = '@' + data.username;
        
        // Risk score
        const riskScore = document.getElementById('riskScore');
        const risk = data.risk_score;
        if (risk > 0.7) {
            riskScore.textContent = 'HIGH RISK';
            riskScore.className = 'risk-badge high';
        } else if (risk > 0.4) {
            riskScore.textContent = 'MEDIUM RISK';
            riskScore.className = 'risk-badge medium';
        } else {
            riskScore.textContent = 'LOW RISK';
            riskScore.className = 'risk-badge low';
        }
        
        // Statistics
        document.getElementById('accountSpamCount').textContent = data.spam_count || 0;
        document.getElementById('accountJudiCount').textContent = data.judi_count || 0;
        document.getElementById('firstSeen').textContent = data.first_seen ? new Date(data.first_seen).toLocaleDateString() : '-';
        document.getElementById('lastSeen').textContent = data.last_seen ? new Date(data.last_seen).toLocaleDateString() : '-';
        
        // Patterns
        const patternsList = document.getElementById('patternsList');
        patternsList.innerHTML = '';
        
        if (data.characteristics) {
            const patterns = data.characteristics.username_patterns || [];
            patterns.forEach(pattern => {
                const div = document.createElement('div');
                div.className = 'pattern-item';
                div.textContent = pattern;
                patternsList.appendChild(div);
            });
            
            // Risk indicators
            const riskIndicatorsList = document.getElementById('riskIndicatorsList');
            riskIndicatorsList.innerHTML = '';
            
            const indicators = data.characteristics.risk_indicators || [];
            indicators.forEach(indicator => {
                const div = document.createElement('div');
                div.className = 'indicator-item';
                div.textContent = indicator;
                riskIndicatorsList.appendChild(div);
            });
        }
    }

    // Load top spammers
    async function loadTopSpammers() {
        try {
            const response = await fetch('/api/top-spammers?limit=10');
            const data = await response.json();

            if (response.ok && data.accounts) {
                const topSpammersTable = document.getElementById('topSpammersTable');
                if (topSpammersTable) {
                    topSpammersTable.innerHTML = '';
                    
                    data.accounts.forEach(account => {
                        const div = document.createElement('div');
                        div.className = 'spammer-row';
                        div.innerHTML = `
                            <span>${account.platform}</span>
                            <span>@${account.username}</span>
                            <span>${account.total_spam} spam</span>
                            <span>Risk: ${(account.risk_score * 100).toFixed(0)}%</span>
                        `;
                        topSpammersTable.appendChild(div);
                    });
                }
            }
        } catch (error) {
            console.error('Error loading top spammers:', error);
        }
    }

    // Update statistics
    async function updateStatistics() {
        // This would fetch and update the statistics
        // For now, using mock data
        const stats = {
            total: parseInt(document.getElementById('totalMessages')?.textContent || 0) + 1,
            spam: parseInt(document.getElementById('spamCount')?.textContent || 0),
            judi: parseInt(document.getElementById('judiCount')?.textContent || 0),
            clean: parseInt(document.getElementById('cleanCount')?.textContent || 0)
        };
        
        // Update based on last detection
        // This would be updated based on actual detection results
        
        if (document.getElementById('totalMessages')) {
            document.getElementById('totalMessages').textContent = stats.total;
        }
    }

    // Update user statistics
    async function updateUserStats() {
        try {
            const response = await fetch('/api/user-stats');
            const data = await response.json();

            if (response.ok) {
                // Update dashboard stats
                document.getElementById('userTotalDetections').textContent = data.total_detections;
                document.getElementById('userSpamCount').textContent = data.spam_count;
                document.getElementById('userJudiCount').textContent = data.judi_count;
                document.getElementById('userDeletedCount').textContent = data.deleted_count;
                
                // Update recent analyses
                const recentAnalysesList = document.getElementById('recentAnalysesList');
                if (recentAnalysesList) {
                    recentAnalysesList.innerHTML = '';
                    
                    data.recent_analyses.forEach(analysis => {
                        const div = document.createElement('div');
                        div.className = 'recent-item';
                        div.innerHTML = `
                            <div class="platform">${analysis.platform}</div>
                            <div class="url">${analysis.url}</div>
                            <div class="stats">Spam: ${analysis.spam_comments}, Judi: ${analysis.judi_comments}</div>
                        `;
                        recentAnalysesList.appendChild(div);
                    });
                }
            }
        } catch (error) {
            console.error('Error loading user stats:', error);
        }
    }

    // Delete all spam (dashboard)
    const deleteAllSpamBtn = document.getElementById('deleteAllSpamBtn');
    deleteAllSpamBtn?.addEventListener('click', async function() {
        if (!confirm('Are you sure you want to delete ALL spam and judi messages?')) {
            return;
        }

        try {
            const response = await fetch('/api/delete-spam', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ category: 'all' })
            });

            const data = await response.json();

            if (response.ok) {
                alert(data.message);
                updateUserStats();
            }
        } catch (error) {
            alert('Error: ' + error.message);
        }
    });

    // Export data
    const exportDataBtn = document.getElementById('exportDataBtn');
    exportDataBtn?.addEventListener('click', function() {
        alert('Export feature coming soon! Your data will be downloadable as JSON/CSV.');
    });

    // Initialize
    loadTopSpammers();
    
    // Load user stats if authenticated
    if (document.querySelector('.user-dashboard')) {
        updateUserStats();
    }

    // Auto-refresh stats every 30 seconds
    setInterval(() => {
        if (document.querySelector('.user-dashboard')) {
            updateUserStats();
        }
    }, 30000);

    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + Enter to analyze
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            const activeTab = document.querySelector('.tab-content.active');
            if (activeTab.id === 'detection-tab' && messageInput.value.trim()) {
                detectBtn.click();
            } else if (activeTab.id === 'social-tab' && socialUrl.value.trim()) {
                analyzeUrlBtn.click();
            }
        }
        
        // Escape to clear
        if (e.key === 'Escape') {
            const activeTab = document.querySelector('.tab-content.active');
            if (activeTab.id === 'detection-tab') {
                clearBtn?.click();
            }
        }
    });
});
