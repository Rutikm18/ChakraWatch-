// ==============================================================================
// ChakraWatch Frontend JavaScript - Improved Version with Better Error Handling
// ==============================================================================

// Global application state
const AppState = {
    currentPage: 1,
    totalPages: 1,
    isLoading: false,
    currentFilters: {},
    viewMode: 'grid',
    darkMode: false,
    articles: [],
    stats: null,
    API_BASE: 'http://localhost:8000',
    retryCount: 0,
    maxRetries: 3
};

// ==============================================================================
// UTILITY FUNCTIONS
// ==============================================================================

const Utils = {
    // Debounce function to limit API calls
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    // Escape HTML to prevent XSS
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text || '';
        return div.innerHTML;
    },

    // Format date for display
    formatDate(dateString) {
        if (!dateString) return 'Unknown date';
        
        try {
            const date = new Date(dateString);
            if (isNaN(date.getTime())) return 'Invalid date';
            
            const now = new Date();
            const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));

            if (diffInHours < 1) return 'Just now';
            if (diffInHours < 24) return `${diffInHours}h ago`;
            if (diffInHours < 48) return 'Yesterday';
            if (diffInHours < 168) return `${Math.floor(diffInHours / 24)}d ago`;
            
            return date.toLocaleDateString('en-US', { 
                month: 'short', 
                day: 'numeric',
                year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
            });
        } catch (e) {
            return 'Invalid date';
        }
    },

    // Format numbers with commas
    formatNumber(num) {
        if (num === null || num === undefined) return '0';
        return Number(num).toLocaleString();
    },

    // Get threat level info
    getThreatInfo(level) {
        const threats = {
            'critical': { emoji: '🔴', color: 'critical' },
            'high': { emoji: '🟠', color: 'high' },
            'medium': { emoji: '🟡', color: 'medium' },
            'low': { emoji: '🟢', color: 'low' }
        };
        return threats[level] || { emoji: '⚪', color: 'unknown' };
    },

    // Get IOC type info
    getIOCInfo(ioc) {
        if (ioc.includes('ip:')) return { emoji: '🌐', type: 'IP Address' };
        if (ioc.includes('domain:')) return { emoji: '🏠', type: 'Domain' };
        if (ioc.includes('hash')) return { emoji: '🔒', type: 'Hash' };
        if (ioc.includes('email:')) return { emoji: '📧', type: 'Email' };
        if (ioc.includes('url:')) return { emoji: '🔗', type: 'URL' };
        if (ioc.includes('cve:')) return { emoji: '🛡️', type: 'CVE' };
        return { emoji: '🎯', type: 'IOC' };
    },

    // Check if we're online
    isOnline() {
        return navigator.onLine;
    }
};

// ==============================================================================
// API SERVICE WITH IMPROVED ERROR HANDLING
// ==============================================================================

const ApiService = {
    async request(endpoint, options = {}) {
        const maxRetries = 3;
        let lastError;

        for (let attempt = 1; attempt <= maxRetries; attempt++) {
            try {
                // Check if we're online first
                if (!Utils.isOnline()) {
                    throw new Error('No internet connection');
                }

                const url = `${AppState.API_BASE}${endpoint}`;
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout

                const response = await fetch(url, {
                    headers: {
                        'Content-Type': 'application/json',
                        ...options.headers
                    },
                    signal: controller.signal,
                    ...options
                });

                clearTimeout(timeoutId);

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                const data = await response.json();
                
                // Reset retry count on success
                AppState.retryCount = 0;
                
                return data;

            } catch (error) {
                lastError = error;
                console.error(`API request attempt ${attempt} failed:`, error);

                if (attempt < maxRetries) {
                    // Wait before retrying (exponential backoff)
                    const delay = Math.pow(2, attempt) * 1000;
                    await new Promise(resolve => setTimeout(resolve, delay));
                    console.log(`Retrying in ${delay}ms...`);
                } else {
                    // All retries failed
                    AppState.retryCount++;
                    this.handleApiError(error, endpoint);
                    throw error;
                }
            }
        }
    },

    handleApiError(error, endpoint) {
        let message = 'An error occurred';
        
        if (error.name === 'AbortError') {
            message = 'Request timed out. Please try again.';
        } else if (error.message.includes('Failed to fetch')) {
            message = 'Unable to connect to server. Please check if the server is running.';
        } else if (error.message.includes('No internet connection')) {
            message = 'No internet connection. Please check your network.';
        } else if (error.message.includes('404')) {
            message = `Endpoint ${endpoint} not found. Server may still be starting.`;
        } else if (error.message.includes('500')) {
            message = 'Server error. Please try again later.';
        }

        NotificationService.show(message, 'error');
    },

    async getHealthCheck() {
        try {
            return await this.request('/health');
        } catch (error) {
            console.error('Health check failed:', error);
            return { status: 'unhealthy', error: error.message };
        }
    },

    async getArticles(page = 1, perPage = 12, filters = {}) {
        const params = new URLSearchParams({
            page: page.toString(),
            per_page: perPage.toString()
        });

        // Add simple filters
        if (filters.threat_level) params.append('threat_level', filters.threat_level);
        if (filters.source) params.append('source', filters.source);

        return this.request(`/articles?${params}`);
    },

    async searchArticles(filters, page = 1, perPage = 12) {
        const params = new URLSearchParams({
            page: page.toString(),
            per_page: perPage.toString()
        });

        return this.request(`/search?${params}`, {
            method: 'POST',
            body: JSON.stringify(filters)
        });
    },

    async getStats() {
        return this.request('/stats');
    },

    async triggerScrape() {
        return this.request('/scrape', { method: 'POST' });
    },

    async analyzeText(text) {
        return this.request('/analyze', {
            method: 'POST',
            body: JSON.stringify({ text })
        });
    }
};

// ==============================================================================
// NOTIFICATION SERVICE
// ==============================================================================

const NotificationService = {
    show(message, type = 'info', duration = 5000) {
        const container = document.getElementById('notificationContainer');
        if (!container) return;

        const notification = document.createElement('div');
        
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <span class="notification-icon">${this.getIcon(type)}</span>
            <span class="notification-message">${Utils.escapeHtml(message)}</span>
        `;

        container.appendChild(notification);

        // Auto remove after duration
        const timeoutId = setTimeout(() => {
            if (notification.parentNode) {
                notification.style.animation = 'slideOut 0.3s ease forwards';
                setTimeout(() => notification.remove(), 300);
            }
        }, duration);

        // Allow manual dismissal
        notification.addEventListener('click', () => {
            clearTimeout(timeoutId);
            notification.style.animation = 'slideOut 0.3s ease forwards';
            setTimeout(() => notification.remove(), 300);
        });

        return notification;
    },

    getIcon(type) {
        const icons = {
            'info': 'ℹ️',
            'success': '✅',
            'error': '❌',
            'warning': '⚠️'
        };
        return icons[type] || 'ℹ️';
    }
};

// ==============================================================================
// LOADING SERVICE
// ==============================================================================

const LoadingService = {
    show() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.classList.add('show');
            AppState.isLoading = true;
        }
    },

    hide() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.classList.remove('show');
            AppState.isLoading = false;
        }
    },

    showInContainer(containerId, message = 'Loading...') {
        const container = document.getElementById(containerId);
        if (!container) return;

        container.innerHTML = `
            <div class="loading-state">
                <div class="loading-spinner"></div>
                <div class="loading-text">${Utils.escapeHtml(message)}</div>
            </div>
        `;
    }
};

// ==============================================================================
// UI COMPONENTS
// ==============================================================================

const UIComponents = {
    createArticleCard(article) {
        const threatInfo = Utils.getThreatInfo(article.threat_level);
        
        return `
            <div class="article-card" data-article-id="${article.id}">
                <div class="article-header">
                    <div class="threat-badge threat-${threatInfo.color}">
                        ${threatInfo.emoji} 
                        ${article.threat_level.toUpperCase()} 
                        (${Math.round((article.confidence_score || 0) * 100)}%)
                    </div>
                    <div class="article-date">
                        <span class="date-icon">🕒</span>
                        ${Utils.formatDate(article.published_date)}
                    </div>
                </div>

                <h3 class="article-title">${Utils.escapeHtml(article.title || 'Untitled')}</h3>
                
                <p class="article-summary">${Utils.escapeHtml(article.summary || 'No summary available')}</p>

                ${this.createTagsSection(article.tags || [])}
                ${this.createIOCsSection(article.iocs || [])}

                <div class="article-footer">
                    <div class="article-source">
                        <span class="source-icon">📡</span>
                        ${Utils.escapeHtml(article.source_name || 'Unknown Source')}
                        ${(article.views > 0) ? `• ${Utils.formatNumber(article.views)} views` : ''}
                    </div>
                    <a href="${article.url}" target="_blank" rel="noopener noreferrer" class="article-link">
                        Read Article
                        <span class="link-icon">↗</span>
                    </a>
                </div>
            </div>
        `;
    },

    createTagsSection(tags) {
        if (!tags || tags.length === 0) return '';
        
        const displayTags = tags.slice(0, 4);
        const remainingCount = tags.length - displayTags.length;
        
        return `
            <div class="article-tags">
                ${displayTags.map(tag => `
                    <span class="tag" onclick="searchByTag('${Utils.escapeHtml(tag)}')">${Utils.escapeHtml(tag)}</span>
                `).join('')}
                ${remainingCount > 0 ? `<span class="tag tag-more">+${remainingCount} more</span>` : ''}
            </div>
        `;
    },

    createIOCsSection(iocs) {
        if (!iocs || iocs.length === 0) return '';
        
        const displayIOCs = iocs.slice(0, 4);
        const remainingCount = iocs.length - displayIOCs.length;
        
        return `
            <div class="iocs-section">
                <div class="iocs-title">
                    <span class="iocs-icon">🎯</span>
                    IOCs Found (${iocs.length})
                </div>
                <div class="iocs-list">
                    ${displayIOCs.map(ioc => {
                        const iocInfo = Utils.getIOCInfo(ioc);
                        const value = (ioc.split(':')[1] || ioc).substring(0, 20);
                        return `
                            <span class="ioc" title="${Utils.escapeHtml(ioc)}">
                                ${iocInfo.emoji} ${Utils.escapeHtml(value)}${value.length === 20 ? '...' : ''}
                            </span>
                        `;
                    }).join('')}
                    ${remainingCount > 0 ? `<span class="ioc ioc-more">+${remainingCount} more</span>` : ''}
                </div>
            </div>
        `;
    },

    createPagination(data) {
        if (data.pages <= 1) return '';
        
        let paginationHTML = '';
        
        // Previous button
        paginationHTML += `
            <button class="page-btn" ${!data.has_prev ? 'disabled' : ''} 
                    onclick="changePage(${data.page - 1})" title="Previous page">
                ← Prev
            </button>
        `;
        
        // Page numbers
        const startPage = Math.max(1, data.page - 2);
        const endPage = Math.min(data.pages, data.page + 2);
        
        if (startPage > 1) {
            paginationHTML += `<button class="page-btn" onclick="changePage(1)">1</button>`;
            if (startPage > 2) {
                paginationHTML += `<span class="page-ellipsis">...</span>`;
            }
        }
        
        for (let i = startPage; i <= endPage; i++) {
            paginationHTML += `
                <button class="page-btn ${i === data.page ? 'active' : ''}" 
                        onclick="changePage(${i})" title="Page ${i}">
                    ${i}
                </button>
            `;
        }
        
        if (endPage < data.pages) {
            if (endPage < data.pages - 1) {
                paginationHTML += `<span class="page-ellipsis">...</span>`;
            }
            paginationHTML += `<button class="page-btn" onclick="changePage(${data.pages})">${data.pages}</button>`;
        }
        
        // Next button
        paginationHTML += `
            <button class="page-btn" ${!data.has_next ? 'disabled' : ''} 
                    onclick="changePage(${data.page + 1})" title="Next page">
                Next →
            </button>
        `;
        
        return paginationHTML;
    },

    createEmptyState(message, action = null) {
        return `
            <div class="empty-state">
                <div class="empty-icon">🔍</div>
                <h3 class="empty-title">No Articles Found</h3>
                <p class="empty-description">${Utils.escapeHtml(message)}</p>
                ${action ? `<button class="btn btn-primary" onclick="${action.callback}">${Utils.escapeHtml(action.text)}</button>` : ''}
            </div>
        `;
    }
};

// ==============================================================================
// DATA MANAGEMENT
// ==============================================================================

const DataManager = {
    async loadStats() {
        try {
            const stats = await ApiService.getStats();
            this.updateStatsDisplay(stats);
            AppState.stats = stats;
        } catch (error) {
            console.error('Failed to load stats:', error);
            this.showStatsError();
        }
    },

    async loadArticles(page = 1) {
        if (AppState.isLoading) return;

        try {
            LoadingService.showInContainer('articlesGrid', 'Loading threat intelligence...');
            
            let response;
            const hasAdvancedFilters = AppState.currentFilters.keywords && AppState.currentFilters.keywords.length > 0;
            
            if (hasAdvancedFilters) {
                response = await ApiService.searchArticles(AppState.currentFilters, page, 12);
            } else {
                response = await ApiService.getArticles(page, 12, AppState.currentFilters);
            }
            
            this.displayArticles(response);
            this.updatePagination(response);
            this.updateArticlesInfo(response);
            
            AppState.articles = response.items || [];
            AppState.currentPage = response.page || 1;
            AppState.totalPages = response.pages || 1;
            
        } catch (error) {
            console.error('Failed to load articles:', error);
            this.showArticlesError();
        }
    },

    updateStatsDisplay(stats) {
        const elements = {
            totalArticles: document.getElementById('totalArticles'),
            criticalThreats: document.getElementById('criticalThreats'),
            iocsFound: document.getElementById('iocsFound'),
            activeSources: document.getElementById('activeSources')
        };

        // Safely update elements
        if (elements.totalArticles) {
            elements.totalArticles.textContent = Utils.formatNumber(stats.total_articles || 0);
        }
        if (elements.criticalThreats) {
            elements.criticalThreats.textContent = Utils.formatNumber(stats.threat_distribution?.critical || 0);
        }
        if (elements.iocsFound) {
            elements.iocsFound.textContent = Utils.formatNumber(stats.articles_with_iocs || 0);
        }
        if (elements.activeSources) {
            const sourceCount = Object.keys(stats.source_distribution || {}).length;
            elements.activeSources.textContent = sourceCount.toString();
        }
    },

    displayArticles(data) {
        const grid = document.getElementById('articlesGrid');
        if (!grid) return;
        
        if (!data.items || data.items.length === 0) {
            grid.innerHTML = UIComponents.createEmptyState(
                'No articles match your current search criteria. Try adjusting your filters or search terms.',
                { text: 'Clear Filters', callback: 'clearFilters()' }
            );
            return;
        }
        
        // Update grid class based on view mode
        grid.className = `articles-grid ${AppState.viewMode === 'list' ? 'list-view' : ''}`;
        
        // Render articles
        grid.innerHTML = data.items.map(article => UIComponents.createArticleCard(article)).join('');
        
        // Add entrance animations
        this.animateArticleCards();
    },

    updatePagination(data) {
        const pagination = document.getElementById('pagination');
        if (!pagination) return;
        
        pagination.innerHTML = UIComponents.createPagination(data);
    },

    updateArticlesInfo(data) {
        const info = document.getElementById('articlesInfo');
        if (!info) return;
        
        const searchInfo = AppState.currentFilters.keywords ? 
            ` for "${AppState.currentFilters.keywords.join(' ')}"` : '';
        
        info.textContent = `Showing ${data.items?.length || 0} of ${Utils.formatNumber(data.total || 0)} articles${searchInfo}`;
    },

    animateArticleCards() {
        const cards = document.querySelectorAll('.article-card');
        cards.forEach((card, index) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                card.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, index * 50);
        });
    },

    showStatsError() {
        const statValues = ['totalArticles', 'criticalThreats', 'iocsFound', 'activeSources'];
        statValues.forEach(id => {
            const element = document.getElementById(id);
            if (element) element.textContent = '—';
        });
    },

    showArticlesError() {
        const grid = document.getElementById('articlesGrid');
        if (!grid) return;
        
        grid.innerHTML = UIComponents.createEmptyState(
            'Failed to load articles. Please check your connection and try again.',
            { text: 'Retry', callback: 'refreshData()' }
        );
    }
};

// ==============================================================================
// SEARCH MANAGEMENT
// ==============================================================================

const SearchManager = {
    init() {
        const searchInput = document.getElementById('searchInput');
        const threatLevelFilter = document.getElementById('threatLevelFilter');
        const sourceFilter = document.getElementById('sourceFilter');
        
        if (!searchInput || !threatLevelFilter || !sourceFilter) {
            console.warn('Search elements not found');
            return;
        }
        
        // Debounced search
        const debouncedSearch = Utils.debounce(() => this.performSearch(), 500);
        searchInput.addEventListener('input', debouncedSearch);
        
        // Filter change handlers
        threatLevelFilter.addEventListener('change', () => this.performSearch());
        sourceFilter.addEventListener('change', () => this.performSearch());
        
        // Search input enhancements
        this.setupSearchEnhancements();
    },

    setupSearchEnhancements() {
        const searchInput = document.getElementById('searchInput');
        const clearBtn = document.getElementById('clearBtn');
        
        if (!searchInput || !clearBtn) return;
        
        searchInput.addEventListener('input', () => {
            clearBtn.style.display = searchInput.value ? 'block' : 'none';
        });
        
        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                this.performSearch();
            } else if (e.key === 'Escape') {
                this.clearSearch();
            }
        });
    },

    performSearch() {
        const searchInput = document.getElementById('searchInput');
        const threatLevelFilter = document.getElementById('threatLevelFilter');
        const sourceFilter = document.getElementById('sourceFilter');
        
        if (!searchInput || !threatLevelFilter || !sourceFilter) return;
        
        const searchValue = searchInput.value.trim();
        const threatLevel = threatLevelFilter.value;
        const source = sourceFilter.value;
        
        // Build filters object
        AppState.currentFilters = {};
        
        if (searchValue) {
            AppState.currentFilters.keywords = searchValue.split(' ').filter(w => w.length > 0);
        }
        if (threatLevel) {
            AppState.currentFilters.threat_level = threatLevel;
            AppState.currentFilters.threat_levels = [threatLevel];
        }
        if (source) {
            AppState.currentFilters.source = source;
            AppState.currentFilters.sources = [source];
        }
        
        // Reset to first page and load
        AppState.currentPage = 1;
        DataManager.loadArticles(1);
        
        // Update URL without reloading page
        this.updateURL();
    },

    clearSearch() {
        const searchInput = document.getElementById('searchInput');
        const clearBtn = document.getElementById('clearBtn');
        
        if (searchInput) searchInput.value = '';
        if (clearBtn) clearBtn.style.display = 'none';
        
        this.performSearch();
    },

    clearFilters() {
        const elements = {
            searchInput: document.getElementById('searchInput'),
            threatLevelFilter: document.getElementById('threatLevelFilter'),
            sourceFilter: document.getElementById('sourceFilter'),
            clearBtn: document.getElementById('clearBtn')
        };
        
        if (elements.searchInput) elements.searchInput.value = '';
        if (elements.threatLevelFilter) elements.threatLevelFilter.value = '';
        if (elements.sourceFilter) elements.sourceFilter.value = '';
        if (elements.clearBtn) elements.clearBtn.style.display = 'none';
        
        AppState.currentFilters = {};
        AppState.currentPage = 1;
        DataManager.loadArticles(1);
        
        NotificationService.show('Filters cleared', 'info');
        this.updateURL();
    },

    updateURL() {
        try {
            const params = new URLSearchParams();
            
            if (AppState.currentFilters.keywords) {
                params.set('q', AppState.currentFilters.keywords.join(' '));
            }
            if (AppState.currentFilters.threat_level) {
                params.set('threat_level', AppState.currentFilters.threat_level);
            }
            if (AppState.currentFilters.source) {
                params.set('source', AppState.currentFilters.source);
            }
            if (AppState.currentPage > 1) {
                params.set('page', AppState.currentPage.toString());
            }
            
            const newURL = params.toString() ? `?${params.toString()}` : window.location.pathname;
            history.replaceState(null, '', newURL);
        } catch (e) {
            console.warn('Failed to update URL:', e);
        }
    },

    loadFromURL() {
        try {
            const params = new URLSearchParams(window.location.search);
            
            const query = params.get('q');
            const threatLevel = params.get('threat_level');
            const source = params.get('source');
            const page = parseInt(params.get('page')) || 1;
            
            const elements = {
                searchInput: document.getElementById('searchInput'),
                threatLevelFilter: document.getElementById('threatLevelFilter'),
                sourceFilter: document.getElementById('sourceFilter')
            };
            
            if (query && elements.searchInput) {
                elements.searchInput.value = query;
                AppState.currentFilters.keywords = query.split(' ').filter(w => w.length > 0);
            }
            if (threatLevel && elements.threatLevelFilter) {
                elements.threatLevelFilter.value = threatLevel;
                AppState.currentFilters.threat_level = threatLevel;
            }
            if (source && elements.sourceFilter) {
                elements.sourceFilter.value = source;
                AppState.currentFilters.source = source;
            }
            
            AppState.currentPage = page;
        } catch (e) {
            console.warn('Failed to load from URL:', e);
        }
    }
};

// ==============================================================================
// THEME MANAGEMENT
// ==============================================================================

const ThemeManager = {
    init() {
        // Load saved theme
        try {
            const savedTheme = localStorage.getItem('chakrawatch_theme');
            if (savedTheme === 'dark') {
                this.enableDarkMode();
            }
        } catch (e) {
            console.warn('Failed to load saved theme:', e);
        }
        
        // Update theme button text
        this.updateThemeButton();
    },

    toggle() {
        if (AppState.darkMode) {
            this.enableLightMode();
        } else {
            this.enableDarkMode();
        }
        
        this.updateThemeButton();
        this.saveThemePreference();
    },

    enableDarkMode() {
        document.body.classList.add('dark');
        AppState.darkMode = true;
        NotificationService.show('Dark mode enabled', 'success');
    },

    enableLightMode() {
        document.body.classList.remove('dark');
        AppState.darkMode = false;
        NotificationService.show('Light mode enabled', 'success');
    },

    updateThemeButton() {
        const btn = document.getElementById('themeBtn');
        if (!btn) return;
        
        const icon = btn.querySelector('.btn-icon');
        const text = btn.querySelector('.btn-text');
        
        if (icon && text) {
            if (AppState.darkMode) {
                icon.textContent = '☀️';
                text.textContent = 'Light';
            } else {
                icon.textContent = '🌙';
                text.textContent = 'Dark';
            }
        }
    },

    saveThemePreference() {
        try {
            localStorage.setItem('chakrawatch_theme', AppState.darkMode ? 'dark' : 'light');
        } catch (e) {
            console.warn('Failed to save theme preference:', e);
        }
    }
};

// ==============================================================================
// GLOBAL FUNCTIONS (called from HTML)
// ==============================================================================

async function refreshData() {
    const btn = document.getElementById('refreshBtn');
    if (!btn) return;
    
    const originalText = btn.querySelector('.btn-text')?.textContent || 'Refresh';
    
    btn.disabled = true;
    const textElement = btn.querySelector('.btn-text');
    if (textElement) textElement.textContent = 'Refreshing...';
    
    try {
        await Promise.all([
            DataManager.loadStats(),
            DataManager.loadArticles(AppState.currentPage)
        ]);
        NotificationService.show('Data refreshed successfully!', 'success');
    } catch (error) {
        NotificationService.show('Failed to refresh data', 'error');
    } finally {
        btn.disabled = false;
        if (textElement) textElement.textContent = originalText;
    }
}

async function triggerScrape() {
    const btn = document.getElementById('scrapeBtn');
    if (!btn) return;
    
    const originalText = btn.querySelector('.btn-text')?.textContent || 'Scrape';
    
    try {
        btn.disabled = true;
        const textElement = btn.querySelector('.btn-text');
        if (textElement) textElement.textContent = 'Scraping...';
        
        await ApiService.triggerScrape();
        NotificationService.show('Scraping initiated! New data will be available shortly.', 'success');
        
        // Refresh data after a delay
        setTimeout(() => {
            refreshData();
        }, 10000);
        
    } catch (error) {
        NotificationService.show('Failed to trigger scraping', 'error');
    } finally {
        btn.disabled = false;
        const textElement = btn.querySelector('.btn-text');
        if (textElement) textElement.textContent = originalText;
    }
}

function toggleDarkMode() {
    ThemeManager.toggle();
}

function searchArticles() {
    SearchManager.performSearch();
}

function clearFilters() {
    SearchManager.clearFilters();
}

function clearSearch() {
    SearchManager.clearSearch();
}

function changePage(page) {
    if (page < 1 || page > AppState.totalPages || AppState.isLoading) return;
    
    AppState.currentPage = page;
    DataManager.loadArticles(page);
    
    // Scroll to top smoothly
    window.scrollTo({ top: 0, behavior: 'smooth' });
    
    // Update URL
    SearchManager.updateURL();
}

function setViewMode(mode) {
    AppState.viewMode = mode;
    
    // Update view buttons
    const viewBtns = document.querySelectorAll('.view-btn');
    viewBtns.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.view === mode);
    });
    
    // Re-render articles with new view mode
    if (AppState.articles.length > 0) {
        const fakeResponse = {
            items: AppState.articles,
            total: AppState.articles.length,
            page: AppState.currentPage,
            pages: AppState.totalPages
        };
        DataManager.displayArticles(fakeResponse);
    }
    
    // Save preference
    try {
        localStorage.setItem('chakrawatch_viewmode', mode);
    } catch (e) {
        console.warn('Failed to save view mode:', e);
    }
}

function searchByTag(tag) {
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.value = tag;
        SearchManager.performSearch();
        NotificationService.show(`Searching for articles tagged with "${tag}"`, 'info');
    }
}

// ==============================================================================
// APPLICATION INITIALIZATION
// ==============================================================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('🛡️ ChakraWatch frontend initializing...');
    
    try {
        // Initialize managers
        ThemeManager.init();
        SearchManager.init();
        
        // Load saved view mode
        try {
            const savedViewMode = localStorage.getItem('chakrawatch_viewmode');
            if (savedViewMode && ['grid', 'list'].includes(savedViewMode)) {
                setViewMode(savedViewMode);
            }
        } catch (e) {
            console.warn('Failed to load saved view mode:', e);
        }
        
        // Load filters from URL
        SearchManager.loadFromURL();
        
        // Initial data load
        DataManager.loadStats();
        DataManager.loadArticles(AppState.currentPage);
        
        // Set up auto-refresh (every 5 minutes)
        setInterval(() => {
            if (!AppState.isLoading && document.visibilityState === 'visible') {
                console.log('🔄 Auto-refreshing stats...');
                DataManager.loadStats();
            }
        }, 300000);
        
        // Handle online/offline events
        window.addEventListener('online', () => {
            NotificationService.show('Connection restored!', 'success');
            refreshData();
        });
        
        window.addEventListener('offline', () => {
            NotificationService.show('You are currently offline', 'warning');
        });
        
        // Handle visibility change (tab focus)
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'visible') {
                // Check if data is stale (more than 10 minutes old)
                const lastUpdate = AppState.stats?.last_updated;
                if (lastUpdate) {
                    const staleTime = new Date(lastUpdate).getTime() + (10 * 60 * 1000);
                    if (Date.now() > staleTime) {
                        console.log('🔄 Data is stale, refreshing...');
                        DataManager.loadStats();
                    }
                }
            }
        });
        
        // Handle keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + K for search focus
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                const searchInput = document.getElementById('searchInput');
                if (searchInput) searchInput.focus();
            }
            
            // R for refresh
            if (e.key === 'r' && !e.ctrlKey && !e.metaKey && document.activeElement.tagName !== 'INPUT') {
                e.preventDefault();
                refreshData();
            }
        });
        
        console.log('✅ ChakraWatch frontend initialized successfully!');
        NotificationService.show('ChakraWatch loaded successfully!', 'success');
        
    } catch (error) {
        console.error('Failed to initialize ChakraWatch:', error);
        NotificationService.show('Failed to initialize application', 'error');
    }
});

// ==============================================================================
// ERROR HANDLING
// ==============================================================================

// Global error handler
window.addEventListener('error', (e) => {
    console.error('Global error:', e.error);
    NotificationService.show('An unexpected error occurred', 'error');
});

// Unhandled promise rejection handler
window.addEventListener('unhandledrejection', (e) => {
    console.error('Unhandled promise rejection:', e.reason);
    NotificationService.show('A network error occurred', 'error');
});

// Export for debugging (only in development)
if (location.hostname === 'localhost' || location.hostname === '127.0.0.1') {
    window.ChakraWatch = {
        AppState,
        ApiService,
        DataManager,
        SearchManager,
        ThemeManager,
        Utils
    };
}