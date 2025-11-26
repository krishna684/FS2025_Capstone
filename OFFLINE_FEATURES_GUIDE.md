# AGBOT Offline Features User Guide

## Overview
AGBOT now works seamlessly even with poor or no internet connection. Your work is never lost, and the app automatically syncs when you're back online.

## Features

### 🔄 Automatic Offline Support
The app automatically detects when you're offline and adjusts its behavior:
- Previously viewed pages load instantly from cache
- Static resources (images, styles, scripts) are cached
- You can continue browsing your scan history offline

### 📸 Image Compression
All images are automatically compressed before upload:
- **Reduces file size by 50-70%**
- Faster uploads, less data usage
- Max resolution: 1920×1920 pixels
- Quality: 85% (excellent quality, smaller size)

**Example:**
- Original: 5 MB photo
- Compressed: 1.5 MB (70% reduction)
- Upload time: 3× faster

### 📦 Offline Image Queue
When you're offline, images are saved locally and uploaded automatically when connection returns:

**How it works:**
1. Take a photo while offline
2. Image is saved to your device
3. You see: "Image queued for upload"
4. When online, images upload automatically
5. You get a notification: "Uploaded 3 queued images"

**Queue Status:**
- View queue count in console
- Automatic retry on connection restore
- No data loss, ever

### 🔁 Smart Retry System
Network requests automatically retry with intelligent backoff:

**Retry Schedule:**
- Attempt 1: Immediate
- Attempt 2: Wait 1 second
- Attempt 3: Wait 2 seconds
- Attempt 4: Wait 4 seconds

**Manual Retry:**
If requests fail, you'll see a notification:
```
┌─────────────────────────────────────┐
│ 3 failed request(s)                 │
│ [Retry All]  [Dismiss]              │
└─────────────────────────────────────┘
```

Click "Retry All" to manually retry failed requests.

## User Experience

### Online Mode (Normal)
```
1. Take photo
2. Image compressed (1-2 seconds)
3. Upload to server (2-3 seconds)
4. Results displayed
```

### Offline Mode
```
1. Take photo
2. Image compressed (1-2 seconds)
3. Saved to local queue
4. Notification: "Image queued for upload"
5. [Later, when online]
6. Automatic upload
7. Notification: "Uploaded queued image"
```

### Poor Connection Mode
```
1. Take photo
2. Image compressed
3. Upload attempt fails
4. Automatic retry (3 attempts)
5. If still fails: Added to queue
6. Notification: "Network error. Image queued."
```

## Visual Indicators

### Connection Status
- 🟢 **Online:** Normal operation
- 🟡 **Poor Connection:** Retrying requests
- 🔴 **Offline:** Queue mode active

### Notifications
- ✅ **Success:** "Connection restored"
- ⚠️ **Warning:** "You are offline. Some features may be limited."
- ❌ **Error:** "Network error. Image queued for upload."
- ℹ️ **Info:** "Uploaded 2 queued images"

## Technical Details

### Storage Limits
- **Service Worker Cache:** ~50 MB (varies by browser)
- **IndexedDB Queue:** ~50 MB (varies by browser)
- **Session Storage:** ~5 MB

### Browser Support
| Feature | Chrome | Firefox | Safari | Edge |
|---------|--------|---------|--------|------|
| Service Worker | ✅ | ✅ | ✅ | ✅ |
| IndexedDB | ✅ | ✅ | ✅ | ✅ |
| Canvas Compression | ✅ | ✅ | ✅ | ✅ |

### Data Usage Comparison
| Scenario | Without Compression | With Compression |
|----------|-------------------|------------------|
| Single photo | 5 MB | 1.5 MB |
| 10 photos | 50 MB | 15 MB |
| 100 photos | 500 MB | 150 MB |

**Savings:** 70% less data usage!

## Troubleshooting

### Images not uploading?
1. Check internet connection
2. Look for retry notification
3. Click "Retry All" if available
4. Check browser console for errors

### Queue not processing?
1. Ensure you're online (check status bar)
2. Refresh the page
3. Check browser console: `getQueueCount()`
4. Manually trigger: `processQueuedImages()`

### Cache taking too much space?
1. Clear browser cache
2. Or use browser DevTools > Application > Clear Storage

### Service Worker not working?
1. Ensure HTTPS (required except on localhost)
2. Check browser console for errors
3. Unregister and re-register:
   ```javascript
   navigator.serviceWorker.getRegistrations()
     .then(regs => regs.forEach(reg => reg.unregister()));
   ```
4. Refresh page

## Developer Tools

### Check Queue Status
Open browser console:
```javascript
// Get queue count
await getQueueCount()

// View pending images
await getPendingImages()

// Manually process queue
await processQueuedImages()

// Clear completed items
await clearCompletedItems()
```

### Check Failed Requests
```javascript
// View failed requests
getFailedRequests()

// Retry specific request
await retryFailedRequest(requestId)

// Retry all
await retryFailedRequests()

// Clear all
clearFailedRequests()
```

### Check Service Worker
```javascript
// Check registration
navigator.serviceWorker.getRegistration()

// Check cache
caches.keys().then(console.log)

// Check cache size
caches.open('agbot-v1-static')
  .then(cache => cache.keys())
  .then(keys => console.log(`${keys.length} items cached`))
```

## Best Practices

### For Users
1. **Take photos in good lighting** - Better compression results
2. **Wait for upload confirmation** - Don't close app immediately
3. **Check queue periodically** - Ensure all images uploaded
4. **Use WiFi when possible** - Faster uploads, no data charges

### For Developers
1. **Test offline mode** - Use DevTools Network tab
2. **Monitor cache size** - Implement cache limits
3. **Handle errors gracefully** - Always provide user feedback
4. **Log important events** - Easier debugging

## FAQ

**Q: Will my photos be lost if I close the browser?**
A: No! Photos are stored in IndexedDB, which persists even after closing the browser.

**Q: How long are photos kept in the queue?**
A: Until successfully uploaded. There's no automatic expiration.

**Q: Can I use the app completely offline?**
A: You can view cached pages and queue images, but analysis requires internet connection.

**Q: Does compression reduce image quality?**
A: Slightly, but it's barely noticeable. We use 85% quality which is excellent.

**Q: What happens if upload fails 3 times?**
A: The image stays in the queue and you can manually retry later.

**Q: Can I disable compression?**
A: Not currently, but it's configurable in the code if needed.

## Summary

AGBOT's offline features ensure:
- ✅ No data loss
- ✅ Automatic sync when online
- ✅ 70% less data usage
- ✅ Faster uploads
- ✅ Works with poor connections
- ✅ Seamless user experience

Your agricultural data is safe, even in remote areas with limited connectivity!
