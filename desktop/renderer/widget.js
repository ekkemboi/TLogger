// TradeLogger Journal - Manual Trade Entry
const API_URL = 'http://localhost:5000/api';

// DOM Elements
const accountSelect = document.getElementById('account-select');
const symbolSelect = document.getElementById('symbol-select');
// const symbolCustom = document.getElementById('symbol-custom');
const directionSelect = document.getElementById('direction');
const outcomeSelect = document.getElementById('outcome');
const entryPriceInput = document.getElementById('entry-price');
const positionSizeInput = document.getElementById('position-size');
const stopLossInput = document.getElementById('stop-loss');
const takeProfitInput = document.getElementById('take-profit');
const notesInput = document.getElementById('notes');
const tradeDateInput = document.getElementById('trade-date');
const screenshotInput = document.getElementById('screenshot');
const confirmBtn = document.getElementById('confirm-btn');
const clearBtn = document.getElementById('clear-btn');
const recentList = document.getElementById('recent-list');
const statusMessage = document.getElementById('status-message');
const partialExitsList = document.getElementById('partial-exits-list');
const addPartialBtn = document.getElementById('add-partial-btn');
const floatBtn = document.getElementById('float-btn');

// Settings Panel Elements - initialized in initSettingsPanel()

// State
let partialExits = [];
let favoritesCache = {};
let isCollapsed = false;

// Initialize
function init() {
    tradeDateInput.value = new Date().toISOString().split('T')[0];
    initTheme();
    loadAccounts();
    loadFavorites();
    loadRecentTrades();
    initSettingsPanel();
    setupEventListeners();
    updateTradeInfoSummary();
}

// Set always on top
function setAlwaysOnTop(enabled) {
    try {
        if (window.electronAPI && window.electronAPI.setAlwaysOnTop) {
            window.electronAPI.setAlwaysOnTop(enabled);
        }
    } catch (e) {
        console.log('setAlwaysOnTop not available');
    }
}

// Theme Management
function initTheme() {
    const darkModeToggle = document.getElementById('dark-mode-toggle');
    
    // Check for saved theme preference or default to dark
    const savedTheme = localStorage.getItem('theme');
    
    if (savedTheme) {
        // Use saved preference
        const isDark = savedTheme === 'dark';
        document.body.dataset.theme = isDark ? 'dark' : 'light';
        if (darkModeToggle) {
            darkModeToggle.checked = isDark;
        }
    } else {
        // Check system preference
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        document.body.dataset.theme = prefersDark ? 'dark' : 'light';
        if (darkModeToggle) {
            darkModeToggle.checked = prefersDark;
        }
    }
}

function toggleTheme(enabled) {
    const isDark = enabled;
    document.body.dataset.theme = isDark ? 'dark' : 'light';
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
}

// Listen for system theme changes
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
    // Only update if user hasn't manually set a preference
    if (!localStorage.getItem('theme')) {
        const darkModeToggle = document.getElementById('dark-mode-toggle');
        const isDark = e.matches;
        document.body.dataset.theme = isDark ? 'dark' : 'light';
        if (darkModeToggle) {
            darkModeToggle.checked = isDark;
        }
    }
});

// Initialize Settings Panel
function initSettingsPanel() {
    const menuBtn = document.getElementById('menu-btn');
    const settingsPanel = document.getElementById('settings-panel');
    const closeSettingsBtn = document.getElementById('close-settings');
    const alwaysOnTopToggle = document.getElementById('always-on-top');
    const darkModeToggle = document.getElementById('dark-mode-toggle');

    // Toggle settings panel
    function toggleSettings() {
        settingsPanel.classList.toggle('open');
    }

    // Add event listeners
    menuBtn.addEventListener('click', toggleSettings);
    closeSettingsBtn.addEventListener('click', toggleSettings);

    // Click outside to close
    document.addEventListener('click', (e) => {
        if (settingsPanel.classList.contains('open') &&
            !settingsPanel.contains(e.target) &&
            !menuBtn.contains(e.target)) {
            toggleSettings();
        }
    });

    // Always on top toggle
    alwaysOnTopToggle.addEventListener('change', (e) => {
        const enabled = e.target.checked;
        localStorage.setItem('alwaysOnTop', enabled);
        setAlwaysOnTop(enabled);
    });

    // Load saved always on top setting
    const alwaysOnTop = localStorage.getItem('alwaysOnTop') === 'true';
    alwaysOnTopToggle.checked = alwaysOnTop;
    setAlwaysOnTop(alwaysOnTop);

    // Dark mode toggle
    darkModeToggle.addEventListener('change', (e) => {
        toggleTheme(e.target.checked);
    });
}

// Toggle Trade Info collapsible section
function toggleTradeInfo() {
    const section = document.getElementById('trade-info-section');
    section.classList.toggle('collapsed');
}

// Update Trade Info summary display
function updateTradeInfoSummary() {
    const date = document.getElementById('trade-date').value || '--';
    const accountEl = document.getElementById('account-select');
    const account = accountEl.selectedOptions[0]?.text?.replace('-- Select Account --', '') || '--';
    const symbolEl = document.getElementById('symbol-select');
    const symbol = symbolEl.value || '--';
    
    document.getElementById('trade-info-summary').textContent = `${date} • ${account.trim()} • ${symbol}`;
}

// Load accounts from API
async function loadAccounts() {
    try {
        const response = await fetch(`${API_URL}/accounts`);
        const data = await response.json();

        const accounts = data.accounts || data;
        accountSelect.innerHTML = '<option value="">-- Select Account --</option>';
        accounts.forEach(account => {
            const option = document.createElement('option');
            option.value = account.id;
            option.textContent = account.name;
            accountSelect.appendChild(option);
        });

        // Auto-select last used account from localStorage
        const savedAccountId = localStorage.getItem('lastAccountId');
        if (savedAccountId && accounts.find(a => a.id === savedAccountId)) {
            accountSelect.value = savedAccountId;
            updateTradeInfoSummary();
        }
    } catch (error) {
        console.error('Failed to load accounts:', error);
    }
}

// Load favorites from API
async function loadFavorites() {
    try {
        const response = await fetch(`${API_URL}/favorites`);
        const data = await response.json();
        
        favoritesCache = {};
        symbolSelect.innerHTML = '<option value="">-- Select Symbol --</option>';
        data.forEach(f => {
            favoritesCache[f.symbol] = f;
            const option = document.createElement('option');
            option.value = f.symbol;
            option.textContent = f.symbol;
            symbolSelect.appendChild(option);
        });

        // Auto-select last used symbol from localStorage
        const savedSymbol = localStorage.getItem('lastSymbol');
        if (savedSymbol && data.find(f => f.symbol === savedSymbol)) {
            symbolSelect.value = savedSymbol;
            updateTradeInfoSummary();
        }
    } catch (error) {
        console.error('Failed to load favorites:', error);
    }
}

// Load recent trades
async function loadRecentTrades() {
    try {
        const response = await fetch(`${API_URL}/trades?per_page=2`);
        const data = await response.json();
        renderRecentTrades(data.trades || []);
    } catch (error) {
        console.error('Failed to load recent trades:', error);
    }
}

// Render recent trades
function renderRecentTrades(trades) {
    if (trades.length === 0) {
        recentList.innerHTML = '<p class="no-trades">No trades yet</p>';
        return;
    }

    recentList.innerHTML = trades.map(t => `
        <div class="recent-item">
            <div class="recent-item-header">
                <span class="symbol">${t.symbol}</span>
                <span class="direction ${t.direction}">${t.direction.toUpperCase()}</span>
                <span class="${t.outcome === 'loss' ? 'pnl-negative' : 'pnl-positive'}">
                    ${t.outcome === 'loss' && t.pnl ? '-$' + t.pnl.toFixed(2) : t.pnl ? '$' + t.pnl.toFixed(2) : '--'}
                </span>
            </div>
            <div class="recent-item-meta">
                <span>${t.entry_price?.toFixed(2)} → ${t.take_profit?.toFixed(2) || t.exit_price?.toFixed(2) || 'N/A'}</span>
                <span>${new Date(t.created_at).toLocaleDateString()}</span>
            </div>
        </div>
    `).join('');
}

// Add partial exit
function addPartialExit() {
    const exit = {
        qty: '',
        exit_price: '',
        fees: '0'
    };
    partialExits.push(exit);
    renderPartialExits();
}

// Render partial exits
function renderPartialExits() {
    if (partialExits.length === 0) {
        partialExitsList.innerHTML = '';
        return;
    }

    partialExitsList.innerHTML = partialExits.map((exit, index) => `
        <div class="partial-exit-item">
            <input type="number" placeholder="Qty" class="partial-qty" value="${exit.qty}" 
                   onchange="updatePartialExit(${index}, 'qty', this.value)">
            <input type="number" placeholder="Exit Price" class="partial-exit-price" value="${exit.exit_price}" step="0.01"
                   onchange="updatePartialExit(${index}, 'exit_price', this.value)">
            <input type="number" placeholder="Fees" class="partial-fees" value="${exit.fees}" step="0.01"
                   onchange="updatePartialExit(${index}, 'fees', this.value)">
            <button class="btn-remove" onclick="removePartialExit(${index})">×</button>
        </div>
    `).join('');
}

// Update partial exit
function updatePartialExit(index, field, value) {
    partialExits[index][field] = value;
}

// Remove partial exit
function removePartialExit(index) {
    partialExits.splice(index, 1);
    renderPartialExits();
}

// Clear form
function clearForm() {
    accountSelect.value = '';
    symbolSelect.value = '';
    directionSelect.value = 'long';
    outcomeSelect.value = 'win';
    entryPriceInput.value = '';
    positionSizeInput.value = '';
    stopLossInput.value = '';
    takeProfitInput.value = '';
    notesInput.value = '';
    screenshotInput.value = '';
    tradeDateInput.value = new Date().toISOString().split('T')[0];
    partialExits = [];
    renderPartialExits();
    hideStatus();
}

// Show status message
function showStatus(message, type = 'success') {
    statusMessage.textContent = message;
    statusMessage.className = `status-message status-${type}`;
    statusMessage.classList.remove('hidden');
    setTimeout(hideStatus, 3000);
}

// Hide status message
function hideStatus() {
    statusMessage.classList.add('hidden');
}

// Confirm trade
async function confirmTrade() {
    const symbol = symbolSelect.value;
    const entryPrice = parseFloat(entryPriceInput.value);
    const positionSize = parseFloat(positionSizeInput.value) || 1;
    const takeProfit = parseFloat(takeProfitInput.value) || null;

    if (!symbol) {
        showStatus('Please select or enter a symbol', 'error');
        return;
    }

    if (!accountSelect.value) {
        showStatus('Please select an account', 'error');
        return;
    }

    if (!entryPrice || entryPrice <= 0) {
        showStatus('Please enter a valid entry price', 'error');
        return;
    }

    // Validate price logic based on direction
    const direction = directionSelect.value;
    if (direction === 'long') {
        if (takeProfit !== null && takeProfit <= entryPrice) {
            showStatus('For LONG trades, take profit must be higher than entry price', 'error');
            return;
        }
        if (stopLossInput.value && parseFloat(stopLossInput.value) >= entryPrice) {
            showStatus('For LONG trades, stop loss must be lower than entry price', 'error');
            return;
        }
    } else if (direction === 'short') {
        if (takeProfit !== null && takeProfit >= entryPrice) {
            showStatus('For SHORT trades, take profit must be lower than entry price', 'error');
            return;
        }
        if (stopLossInput.value && parseFloat(stopLossInput.value) <= entryPrice) {
            showStatus('For SHORT trades, stop loss must be higher than entry price', 'error');
            return;
        }
    }

    // Build exit transactions from partial exits
    let exitTransactions = [];
    if (partialExits.length > 0) {
        exitTransactions = partialExits.filter(e => e.qty && e.exit_price).map(e => ({
            qty: parseFloat(e.qty),
            exit_price: parseFloat(e.exit_price),
            fees: parseFloat(e.fees) || 0
        }));
    }

    // Get point value and fees from favorite
    const favorite = favoritesCache[symbol.toUpperCase()] || {};
    const pointValue = favorite.point_value || 1;
    const fees = favorite.fees || 0;

    const tradeData = {
        account_id: accountSelect.value,
        symbol: symbol.toUpperCase(),
        direction: directionSelect.value,
        entry_price: entryPrice,
        position_size: positionSize,
        take_profit: takeProfit,
        stop_loss: parseFloat(stopLossInput.value) || null,
        notes: notesInput.value || null,
        trade_date: tradeDateInput.value,
        exit_transactions: exitTransactions.length > 0 ? exitTransactions : null,
        outcome: outcomeSelect.value,
    };

    try {
        const formData = new FormData();
        Object.keys(tradeData).forEach(key => {
            if (tradeData[key] !== null && tradeData[key] !== undefined) {
                if (Array.isArray(tradeData[key])) {
                    formData.append(key, JSON.stringify(tradeData[key]));
                } else {
                    formData.append(key, tradeData[key]);
                }
            }
        });

        const screenshotFile = screenshotInput.files[0];
        if (screenshotFile) {
            formData.append('screenshot', screenshotFile);
        }

        const response = await fetch(`${API_URL}/trades`, {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            const savedTrade = await response.json();
            showStatus(`Trade saved! P&L: $${savedTrade.pnl?.toFixed(2) || 'N/A'}`, 'success');
            clearForm();
            loadRecentTrades();
            // Auto-collapse Trade Info section after save
            const tradeInfoSection = document.getElementById('trade-info-section');
            if (!tradeInfoSection.classList.contains('collapsed')) {
                tradeInfoSection.classList.add('collapsed');
            }
        } else {
            const error = await response.json();
            showStatus(error.error || 'Failed to save trade', 'error');
        }
    } catch (error) {
        console.error('Failed to save trade:', error);
        showStatus('Failed to save trade. Make sure the backend is running.', 'error');
    }
}

// Toggle floating/collapsed mode
async function toggleFloat() {
    const widget = document.querySelector('.widget');
    isCollapsed = !isCollapsed;

    if (isCollapsed) {
        widget.classList.add('collapsed');
        floatBtn.textContent = '▲';
        floatBtn.title = 'Expand widget';
        // Resize window to header-only height
        try {
            if (window.electronAPI && window.electronAPI.resizeWindow) {
                await window.electronAPI.resizeWindow(48);
            }
        } catch (e) {
            console.log('resizeWindow not available:', e.message);
        }
    } else {
        widget.classList.remove('collapsed');
        floatBtn.textContent = '▼';
        floatBtn.title = 'Minimize';
        // Restore full height
        try {
            if (window.electronAPI && window.electronAPI.resizeWindow) {
                await window.electronAPI.resizeWindow(700);
            }
        } catch (e) {
            console.log('resizeWindow not available:', e.message);
        }
    }
}

// Event listeners
function setupEventListeners() {
    confirmBtn.addEventListener('click', confirmTrade);
    clearBtn.addEventListener('click', clearForm);
    addPartialBtn.addEventListener('click', addPartialExit);
    floatBtn.addEventListener('click', (e) => {
        e.stopPropagation();  // Prevent settings menu from closing
        toggleFloat();
    });

    // Save account to localStorage when changed
    accountSelect.addEventListener('change', () => {
        if (accountSelect.value) {
            localStorage.setItem('lastAccountId', accountSelect.value);
            updateTradeInfoSummary();
        }
    });

    // Save symbol to localStorage when changed
    symbolSelect.addEventListener('change', () => {
        if (symbolSelect.value) {
            localStorage.setItem('lastSymbol', symbolSelect.value);
            updateTradeInfoSummary();
        }
    });

    // Window controls
    document.getElementById('close-btn').addEventListener('click', (e) => {
        e.stopPropagation();  // Prevent settings menu from closing first
        if (confirm('Close TradeLogger?')) {
            try {
                if (window.electronAPI && window.electronAPI.closeWindow) {
                    window.electronAPI.closeWindow();
                } else {
                    window.close(); // Fallback for browser testing
                }
            } catch (err) {
                console.log('Close window error:', err.message);
                window.close(); // Fallback for browser testing
            }
        }
    });

    document.getElementById('minimize-btn').addEventListener('click', (e) => {
        e.stopPropagation();  // Prevent settings menu from closing
        try {
            if (window.electronAPI && window.electronAPI.minimizeWindow) {
                window.electronAPI.minimizeWindow();
            }
        } catch (err) {
            console.log('Minimize window error:', err.message);
        }
    });

    document.getElementById('view-more-btn').addEventListener('click', () => {
        try {
            if (window.electronAPI && window.electronAPI.openExternal) {
                window.electronAPI.openExternal('http://localhost:5000/trades');
            } else {
                window.open('http://localhost:5000/trades', '_blank');
            }
        } catch (e) {
            window.open('http://localhost:5000/trades', '_blank');
        }
    });
}

// Initialize on load
init();
