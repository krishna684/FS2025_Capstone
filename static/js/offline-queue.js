// Offline image queuing using IndexedDB

const DB_NAME = 'agbot-offline';
const DB_VERSION = 1;
const STORE_NAME = 'image-queue';

let db = null;

/**
 * Initialize IndexedDB
 * @returns {Promise<IDBDatabase>}
 */
async function initDB() {
    if (db) {
        return db;
    }

    return new Promise((resolve, reject) => {
        const request = indexedDB.open(DB_NAME, DB_VERSION);

        request.onerror = () => {
            console.error('[IndexedDB] Failed to open database:', request.error);
            reject(request.error);
        };

        request.onsuccess = () => {
            db = request.result;
            console.log('[IndexedDB] Database opened successfully');
            resolve(db);
        };

        request.onupgradeneeded = (event) => {
            const db = event.target.result;
            
            // Create object store if it doesn't exist
            if (!db.objectStoreNames.contains(STORE_NAME)) {
                const objectStore = db.createObjectStore(STORE_NAME, { 
                    keyPath: 'id', 
                    autoIncrement: true 
                });
                
                // Create indexes
                objectStore.createIndex('timestamp', 'timestamp', { unique: false });
                objectStore.createIndex('status', 'status', { unique: false });
                
                console.log('[IndexedDB] Object store created');
            }
        };
    });
}

/**
 * Add image to offline queue
 * @param {string} imageData - Base64 image data
 * @param {Object} metadata - Additional metadata
 * @returns {Promise<number>} - ID of queued item
 */
async function queueImage(imageData, metadata = {}) {
    const database = await initDB();
    
    return new Promise((resolve, reject) => {
        const transaction = database.transaction([STORE_NAME], 'readwrite');
        const store = transaction.objectStore(STORE_NAME);
        
        const queueItem = {
            imageData,
            metadata,
            timestamp: Date.now(),
            status: 'pending',
            retryCount: 0
        };
        
        const request = store.add(queueItem);
        
        request.onsuccess = () => {
            console.log('[Queue] Image queued with ID:', request.result);
            resolve(request.result);
        };
        
        request.onerror = () => {
            console.error('[Queue] Failed to queue image:', request.error);
            reject(request.error);
        };
    });
}

/**
 * Get all pending images from queue
 * @returns {Promise<Array>}
 */
async function getPendingImages() {
    const database = await initDB();
    
    return new Promise((resolve, reject) => {
        const transaction = database.transaction([STORE_NAME], 'readonly');
        const store = transaction.objectStore(STORE_NAME);
        const index = store.index('status');
        
        const request = index.getAll('pending');
        
        request.onsuccess = () => {
            resolve(request.result);
        };
        
        request.onerror = () => {
            console.error('[Queue] Failed to get pending images:', request.error);
            reject(request.error);
        };
    });
}

/**
 * Update queue item status
 * @param {number} id - Item ID
 * @param {string} status - New status ('pending', 'uploading', 'completed', 'failed')
 * @returns {Promise<void>}
 */
async function updateQueueItemStatus(id, status) {
    const database = await initDB();
    
    return new Promise((resolve, reject) => {
        const transaction = database.transaction([STORE_NAME], 'readwrite');
        const store = transaction.objectStore(STORE_NAME);
        
        const getRequest = store.get(id);
        
        getRequest.onsuccess = () => {
            const item = getRequest.result;
            if (item) {
                item.status = status;
                item.lastUpdated = Date.now();
                
                const updateRequest = store.put(item);
                
                updateRequest.onsuccess = () => {
                    resolve();
                };
                
                updateRequest.onerror = () => {
                    reject(updateRequest.error);
                };
            } else {
                reject(new Error('Item not found'));
            }
        };
        
        getRequest.onerror = () => {
            reject(getRequest.error);
        };
    });
}

/**
 * Remove item from queue
 * @param {number} id - Item ID
 * @returns {Promise<void>}
 */
async function removeFromQueue(id) {
    const database = await initDB();
    
    return new Promise((resolve, reject) => {
        const transaction = database.transaction([STORE_NAME], 'readwrite');
        const store = transaction.objectStore(STORE_NAME);
        
        const request = store.delete(id);
        
        request.onsuccess = () => {
            console.log('[Queue] Item removed:', id);
            resolve();
        };
        
        request.onerror = () => {
            console.error('[Queue] Failed to remove item:', request.error);
            reject(request.error);
        };
    });
}

/**
 * Get queue count
 * @returns {Promise<number>}
 */
async function getQueueCount() {
    const database = await initDB();
    
    return new Promise((resolve, reject) => {
        const transaction = database.transaction([STORE_NAME], 'readonly');
        const store = transaction.objectStore(STORE_NAME);
        
        const request = store.count();
        
        request.onsuccess = () => {
            resolve(request.result);
        };
        
        request.onerror = () => {
            reject(request.error);
        };
    });
}

/**
 * Process queued images - upload them when online
 * @returns {Promise<{success: number, failed: number}>}
 */
async function processQueuedImages() {
    if (!navigator.onLine) {
        console.log('[Queue] Offline, skipping queue processing');
        return { success: 0, failed: 0 };
    }
    
    const pendingImages = await getPendingImages();
    
    if (pendingImages.length === 0) {
        console.log('[Queue] No pending images to process');
        return { success: 0, failed: 0 };
    }
    
    console.log(`[Queue] Processing ${pendingImages.length} queued images`);
    
    let successCount = 0;
    let failedCount = 0;
    
    for (const item of pendingImages) {
        try {
            await updateQueueItemStatus(item.id, 'uploading');
            
            // Upload image
            const response = await fetch('/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    image_data: item.imageData,
                    metadata: item.metadata
                })
            });
            
            if (response.ok) {
                await removeFromQueue(item.id);
                successCount++;
                console.log(`[Queue] Successfully uploaded image ${item.id}`);
                
                // Show success notification
                if (typeof showToast === 'function') {
                    showToast(`Uploaded queued image (${successCount}/${pendingImages.length})`, 'success');
                }
            } else {
                await updateQueueItemStatus(item.id, 'failed');
                failedCount++;
                console.error(`[Queue] Failed to upload image ${item.id}:`, response.status);
            }
        } catch (error) {
            await updateQueueItemStatus(item.id, 'failed');
            failedCount++;
            console.error(`[Queue] Error uploading image ${item.id}:`, error);
        }
    }
    
    if (successCount > 0 && typeof showToast === 'function') {
        showToast(`Successfully uploaded ${successCount} queued image(s)`, 'success');
    }
    
    if (failedCount > 0 && typeof showToast === 'function') {
        showToast(`Failed to upload ${failedCount} image(s)`, 'error');
    }
    
    return { success: successCount, failed: failedCount };
}

/**
 * Clear all completed items from queue
 * @returns {Promise<number>} - Number of items cleared
 */
async function clearCompletedItems() {
    const database = await initDB();
    
    return new Promise((resolve, reject) => {
        const transaction = database.transaction([STORE_NAME], 'readwrite');
        const store = transaction.objectStore(STORE_NAME);
        const index = store.index('status');
        
        const request = index.openCursor('completed');
        let count = 0;
        
        request.onsuccess = (event) => {
            const cursor = event.target.result;
            if (cursor) {
                cursor.delete();
                count++;
                cursor.continue();
            } else {
                console.log(`[Queue] Cleared ${count} completed items`);
                resolve(count);
            }
        };
        
        request.onerror = () => {
            reject(request.error);
        };
    });
}

// Initialize database on load
if (typeof window !== 'undefined') {
    initDB().catch(error => {
        console.error('[IndexedDB] Initialization failed:', error);
    });
}

// Export functions
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        initDB,
        queueImage,
        getPendingImages,
        updateQueueItemStatus,
        removeFromQueue,
        getQueueCount,
        processQueuedImages,
        clearCompletedItems
    };
}
