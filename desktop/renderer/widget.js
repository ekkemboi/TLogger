// TradeLogger Journal - Manual Trade Entry
const API_URL = 'http://localhost:5000/api';

// DOM Elements
const symbolSelect = document.getElementById('symbol-select');
const symbolCustom = document.getElementById('symbol-custom');
const directionSelect = document.getElementById('direction');
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

// State
let partialExits = [];
let favoritesCache = {};

// Initialize
function init() {
    tradeDateInput.value = new Date().toISOString().split('T')[0];
    loadFavorites();
    loadRecentTrades();
    setupEventListeners();
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
    } catch (error) {
        console.error('Failed to load favorites:', error);
    }
}

// Load recent trades
async function loadRecentTrades() {
    try {
        const response = await fetch(`${API_URL}/trades?per_page=5`);
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
                <span class="${t.pnl >= 0 ? 'pnl-positive' : 'pnl-negative'}">$${t.pnl?.toFixed(2) || '--'}</span>
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
    symbolSelect.value = '';
    symbolCustom.value = '';
    directionSelect.value = 'long';
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
    const symbol = symbolCustom.value.trim() || symbolSelect.value;
    const entryPrice = parseFloat(entryPriceInput.value);
    const positionSize = parseFloat(positionSizeInput.value) || 1;
    const takeProfit = parseFloat(takeProfitInput.value) || null;

    if (!symbol) {
        showStatus('Please select or enter a symbol', 'error');
        return;
    }

    if (!entryPrice || entryPrice <= 0) {
        showStatus('Please enter a valid entry price', 'error');
        return;
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
        symbol: symbol.toUpperCase(),
        direction: directionSelect.value,
        entry_price: entryPrice,
        position_size: positionSize,
        take_profit: takeProfit,
        stop_loss: parseFloat(stopLossInput.value) || null,
        notes: notesInput.value || null,
        trade_date: tradeDateInput.value,
        exit_transactions: exitTransactions.length > 0 ? exitTransactions : null
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
        } else {
            const error = await response.json();
            showStatus(error.error || 'Failed to save trade', 'error');
        }
    } catch (error) {
        console.error('Failed to save trade:', error);
        showStatus('Failed to save trade. Make sure the backend is running.', 'error');
    }
}

// Event listeners
function setupEventListeners() {
    confirmBtn.addEventListener('click', confirmTrade);
    clearBtn.addEventListener('click', clearForm);
    addPartialBtn.addEventListener('click', addPartialExit);
    
    // Symbol selection
    symbolSelect.addEventListener('change', () => {
        if (symbolSelect.value) {
            symbolCustom.value = '';
        }
    });

    // Window controls
    document.getElementById('close-btn').addEventListener('click', () => {
        if (confirm('Close TradeLogger?')) {
            window.close();
        }
    });

    document.getElementById('minimize-btn').addEventListener('click', () => {
        // Electron handles this via main.js
    });
}

// Initialize on load
init();
