// Request retry mechanism with exponential backoff

/**
 * Retry configuration
 */
const RETRY_CONFIG = {
    maxRetries: 3,
    initialDelay: 1000, // 1 second
    maxDelay: 10000, // 10 seconds
    backoffMultiplier: 2
};

/**
 * Calculate delay for exponential backoff
 * @param {number} retryCount - Current retry attempt
 * @returns {number} - Delay in milliseconds
 */
function calculateBackoffDelay(retryCount) {
    const delay = RETRY_CONFIG.initialDelay * Math.pow(RETRY_CONFIG.backoffMultiplier, retryCount);
    return Math.min(delay, RETRY_CONFIG.maxDelay);
}

/**
 * Sleep for specified milliseconds
 * @param {number} ms - Milliseconds to sleep
 * @returns {Promise<void>}
 */
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Fetch with retry logic and exponential backoff
 * @param {string} url - Request URL
 * @param {Object} options - Fetch options
 * @param {number} maxRetries - Maximum retry attempts
 * @returns {Promise<Response>}
 */
async function fetchWithRetry(url, options = {}, maxRetries = RETRY_CONFIG.maxRetries) {
    let lastError;
    
    for (let attempt = 0; attempt <= maxRetries; attempt++) {
        try {
            console.log(`[Retry] Attempt ${attempt + 1}/${maxRetries + 1} for ${url}`);
            
            const response = await fetch(url, options);
            
            // Return successful responses
            if (response.ok) {
                return response;
            }
            
            // Don't retry client errors (4xx) except 408 (timeout) and 429 (rate limit)
            if (response.status >= 400 && response.status < 500) {
                if (response.status !== 408 && response.status !== 429) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
            }
            
            lastError = new Error(`HTTP ${response.status}: ${response.statusText}`);
            
        } catch (error) {
            lastError = error;
            console.error(`[Retry] Attempt ${attempt + 1} failed:`, error.message);
        }
        
        // Don't wait after the last attempt
        if (attempt < maxRetries) {
            const delay = calculateBackoffDelay(attempt);
            console.log(`[Retry] Waiting ${delay}ms before next attempt`);
            await sleep(delay);
        }
    }
    
    // All retries failed
    throw lastError;
}

/**
 * Store failed request in sessionStorage for manual retry
 * @param {string} url - Request URL
 * @param {Object} options - Fetch options
 * @param {string} context - Context description
 */
function storeFailedRequest(url, options, context = '') {
    try {
        const failedRequests = getFailedRequests();
        
        const requestData = {
            id: Date.now(),
            url,
            options: {
                method: options.method || 'GET',
                headers: options.headers || {},
                body: options.body || null
            },
            context,
            timestamp: Date.now()
        };
        
        failedRequests.push(requestData);
        sessionStorage.setItem('failedRequests', JSON.stringify(failedRequests));
        
        console.log('[Retry] Stored failed request:', requestData.id);
    } catch (error) {
        console.error('[Retry] Failed to store request:', error);
    }
}

/**
 * Get all failed requests from sessionStorage
 * @returns {Array}
 */
function getFailedRequests() {
    try {
        const stored = sessionStorage.getItem('failedRequests');
        return stored ? JSON.parse(stored) : [];
    } catch (error) {
        console.error('[Retry] Failed to get stored requests:', error);
        return [];
    }
}

/**
 * Remove failed request from storage
 * @param {number} requestId - Request ID
 */
function removeFailedRequest(requestId) {
    try {
        const failedRequests = getFailedRequests();
        const filtered = failedRequests.filter(req => req.id !== requestId);
        sessionStorage.setItem('failedRequests', JSON.stringify(filtered));
        console.log('[Retry] Removed failed request:', requestId);
    } catch (error) {
        console.error('[Retry] Failed to remove request:', error);
    }
}

/**
 * Clear all failed requests
 */
function clearFailedRequests() {
    try {
        sessionStorage.removeItem('failedRequests');
        console.log('[Retry] Cleared all failed requests');
    } catch (error) {
        console.error('[Retry] Failed to clear requests:', error);
    }
}

/**
 * Retry a specific failed request
 * @param {number} requestId - Request ID
 * @returns {Promise<Response>}
 */
async function retryFailedRequest(requestId) {
    const failedRequests = getFailedRequests();
    const request = failedRequests.find(req => req.id === requestId);
    
    if (!request) {
        throw new Error('Request not found');
    }
    
    try {
        console.log('[Retry] Retrying request:', requestId);
        const response = await fetchWithRetry(request.url, request.options);
        
        // Remove from storage on success
        removeFailedRequest(requestId);
        
        return response;
    } catch (error) {
        console.error('[Retry] Retry failed:', error);
        throw error;
    }
}

/**
 * Retry all failed requests
 * @returns {Promise<{success: number, failed: number}>}
 */
async function retryFailedRequests() {
    const failedRequests = getFailedRequests();
    
    if (failedRequests.length === 0) {
        console.log('[Retry] No failed requests to retry');
        return { success: 0, failed: 0 };
    }
    
    console.log(`[Retry] Retrying ${failedRequests.length} failed request(s)`);
    
    let successCount = 0;
    let failedCount = 0;
    
    for (const request of failedRequests) {
        try {
            await retryFailedRequest(request.id);
            successCount++;
        } catch (error) {
            failedCount++;
        }
    }
    
    if (successCount > 0 && typeof showToast === 'function') {
        showToast(`Successfully retried ${successCount} request(s)`, 'success');
    }
    
    if (failedCount > 0 && typeof showToast === 'function') {
        showToast(`${failedCount} request(s) still failed`, 'error');
    }
    
    return { success: successCount, failed: failedCount };
}

/**
 * Show retry UI for failed requests
 */
function showRetryUI() {
    const failedRequests = getFailedRequests();
    
    if (failedRequests.length === 0) {
        return;
    }
    
    // Create retry notification
    const retryDiv = document.createElement('div');
    retryDiv.id = 'retry-notification';
    retryDiv.style.cssText = `
        position: fixed;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        background: #ef4444;
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        z-index: 2000;
        display: flex;
        align-items: center;
        gap: 1rem;
    `;
    
    retryDiv.innerHTML = `
        <span>${failedRequests.length} failed request(s)</span>
        <button id="retry-all-btn" style="
            background: white;
            color: #ef4444;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 0.25rem;
            cursor: pointer;
            font-weight: 600;
        ">Retry All</button>
        <button id="dismiss-retry-btn" style="
            background: transparent;
            color: white;
            border: 1px solid white;
            padding: 0.5rem 1rem;
            border-radius: 0.25rem;
            cursor: pointer;
        ">Dismiss</button>
    `;
    
    document.body.appendChild(retryDiv);
    
    // Add event listeners
    document.getElementById('retry-all-btn').addEventListener('click', async () => {
        retryDiv.remove();
        await retryFailedRequests();
    });
    
    document.getElementById('dismiss-retry-btn').addEventListener('click', () => {
        retryDiv.remove();
    });
}

/**
 * Enhanced API call with retry logic
 * @param {string} endpoint - API endpoint
 * @param {string} method - HTTP method
 * @param {Object} data - Request data
 * @param {Object} options - Additional options
 * @returns {Promise<any>}
 */
async function apiCallWithRetry(endpoint, method = 'GET', data = null, options = {}) {
    const fetchOptions = {
        method,
        headers: {
            'Content-Type': 'application/json',
            ...options.headers
        }
    };
    
    if (data) {
        fetchOptions.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetchWithRetry(endpoint, fetchOptions, options.maxRetries);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('[API] Call failed:', error);
        
        // Store for manual retry
        storeFailedRequest(endpoint, fetchOptions, options.context || '');
        
        // Show retry UI
        showRetryUI();
        
        throw error;
    }
}

// Show retry UI on page load if there are failed requests
if (typeof window !== 'undefined') {
    window.addEventListener('load', () => {
        const failedRequests = getFailedRequests();
        if (failedRequests.length > 0) {
            showRetryUI();
        }
    });
}

// Export functions
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        fetchWithRetry,
        storeFailedRequest,
        getFailedRequests,
        removeFailedRequest,
        clearFailedRequests,
        retryFailedRequest,
        retryFailedRequests,
        showRetryUI,
        apiCallWithRetry
    };
}
