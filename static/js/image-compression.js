// Client-side image compression using Canvas API

/**
 * Compress an image file before upload
 * @param {File|Blob} file - The image file to compress
 * @param {Object} options - Compression options
 * @param {number} options.maxWidth - Maximum width (default: 1920)
 * @param {number} options.maxHeight - Maximum height (default: 1920)
 * @param {number} options.quality - JPEG quality 0-1 (default: 0.85)
 * @returns {Promise<Blob>} - Compressed image blob
 */
async function compressImage(file, options = {}) {
    const {
        maxWidth = 1920,
        maxHeight = 1920,
        quality = 0.85
    } = options;

    return new Promise((resolve, reject) => {
        // Validate input
        if (!file || !file.type.startsWith('image/')) {
            reject(new Error('Invalid image file'));
            return;
        }

        const reader = new FileReader();
        
        reader.onerror = () => {
            reject(new Error('Failed to read image file'));
        };
        
        reader.onload = (e) => {
            const img = new Image();
            
            img.onerror = () => {
                reject(new Error('Failed to load image'));
            };
            
            img.onload = () => {
                try {
                    // Calculate new dimensions while maintaining aspect ratio
                    let width = img.width;
                    let height = img.height;
                    
                    if (width > maxWidth || height > maxHeight) {
                        const aspectRatio = width / height;
                        
                        if (width > height) {
                            width = maxWidth;
                            height = width / aspectRatio;
                        } else {
                            height = maxHeight;
                            width = height * aspectRatio;
                        }
                    }
                    
                    // Create canvas and draw resized image
                    const canvas = document.createElement('canvas');
                    canvas.width = width;
                    canvas.height = height;
                    
                    const ctx = canvas.getContext('2d');
                    
                    // Use better image smoothing
                    ctx.imageSmoothingEnabled = true;
                    ctx.imageSmoothingQuality = 'high';
                    
                    // Draw image
                    ctx.drawImage(img, 0, 0, width, height);
                    
                    // Convert to blob
                    canvas.toBlob(
                        (blob) => {
                            if (blob) {
                                console.log(`[Compression] Original: ${(file.size / 1024).toFixed(2)} KB, Compressed: ${(blob.size / 1024).toFixed(2)} KB`);
                                console.log(`[Compression] Reduction: ${(((file.size - blob.size) / file.size) * 100).toFixed(1)}%`);
                                resolve(blob);
                            } else {
                                reject(new Error('Failed to create compressed image'));
                            }
                        },
                        'image/jpeg',
                        quality
                    );
                } catch (error) {
                    reject(error);
                }
            };
            
            img.src = e.target.result;
        };
        
        reader.readAsDataURL(file);
    });
}

/**
 * Compress image from data URL
 * @param {string} dataUrl - Base64 data URL of the image
 * @param {Object} options - Compression options
 * @returns {Promise<string>} - Compressed image as data URL
 */
async function compressImageFromDataUrl(dataUrl, options = {}) {
    const {
        maxWidth = 1920,
        maxHeight = 1920,
        quality = 0.85
    } = options;

    return new Promise((resolve, reject) => {
        const img = new Image();
        
        img.onerror = () => {
            reject(new Error('Failed to load image from data URL'));
        };
        
        img.onload = () => {
            try {
                // Calculate new dimensions
                let width = img.width;
                let height = img.height;
                
                if (width > maxWidth || height > maxHeight) {
                    const aspectRatio = width / height;
                    
                    if (width > height) {
                        width = maxWidth;
                        height = width / aspectRatio;
                    } else {
                        height = maxHeight;
                        width = height * aspectRatio;
                    }
                }
                
                // Create canvas
                const canvas = document.createElement('canvas');
                canvas.width = width;
                canvas.height = height;
                
                const ctx = canvas.getContext('2d');
                ctx.imageSmoothingEnabled = true;
                ctx.imageSmoothingQuality = 'high';
                
                // Draw and compress
                ctx.drawImage(img, 0, 0, width, height);
                
                const compressedDataUrl = canvas.toDataURL('image/jpeg', quality);
                
                // Log compression stats
                const originalSize = dataUrl.length;
                const compressedSize = compressedDataUrl.length;
                console.log(`[Compression] Original: ${(originalSize / 1024).toFixed(2)} KB, Compressed: ${(compressedSize / 1024).toFixed(2)} KB`);
                console.log(`[Compression] Reduction: ${(((originalSize - compressedSize) / originalSize) * 100).toFixed(1)}%`);
                
                resolve(compressedDataUrl);
            } catch (error) {
                reject(error);
            }
        };
        
        img.src = dataUrl;
    });
}

/**
 * Get image dimensions without loading full image
 * @param {File} file - Image file
 * @returns {Promise<{width: number, height: number}>}
 */
async function getImageDimensions(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        
        reader.onerror = () => reject(new Error('Failed to read file'));
        
        reader.onload = (e) => {
            const img = new Image();
            
            img.onerror = () => reject(new Error('Failed to load image'));
            
            img.onload = () => {
                resolve({
                    width: img.width,
                    height: img.height
                });
            };
            
            img.src = e.target.result;
        };
        
        reader.readAsDataURL(file);
    });
}

// Export functions
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        compressImage,
        compressImageFromDataUrl,
        getImageDimensions
    };
}
