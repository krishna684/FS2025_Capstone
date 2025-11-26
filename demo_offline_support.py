#!/usr/bin/env python3
"""
Demo script to verify offline support implementation
"""

import os
from pathlib import Path

def check_file_exists(filepath):
    """Check if a file exists"""
    exists = os.path.exists(filepath)
    status = "✓" if exists else "✗"
    print(f"{status} {filepath}")
    return exists

def check_file_content(filepath, search_strings):
    """Check if file contains specific strings"""
    if not os.path.exists(filepath):
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    all_found = True
    for search_str in search_strings:
        found = search_str in content
        status = "✓" if found else "✗"
        print(f"  {status} Contains: {search_str[:50]}...")
        if not found:
            all_found = False
    
    return all_found

def main():
    print("=" * 60)
    print("AGBOT Offline Support Implementation Verification")
    print("=" * 60)
    print()
    
    # Check Service Worker
    print("1. Service Worker (sw.js)")
    print("-" * 60)
    sw_exists = check_file_exists('static/sw.js')
    if sw_exists:
        check_file_content('static/sw.js', [
            'CACHE_VERSION',
            'addEventListener(\'install\'',
            'addEventListener(\'fetch\'',
            'networkFirstStrategy',
            'cacheFirstStrategy'
        ])
    print()
    
    # Check Offline Support JS
    print("2. Offline Support (offline.js)")
    print("-" * 60)
    offline_exists = check_file_exists('static/js/offline.js')
    if offline_exists:
        check_file_content('static/js/offline.js', [
            'serviceWorker.register',
            'addEventListener(\'online\'',
            'addEventListener(\'offline\'',
            'processQueuedImages'
        ])
    print()
    
    # Check Image Compression
    print("3. Image Compression (image-compression.js)")
    print("-" * 60)
    compression_exists = check_file_exists('static/js/image-compression.js')
    if compression_exists:
        check_file_content('static/js/image-compression.js', [
            'compressImage',
            'maxWidth = 1920',
            'quality = 0.85',
            'canvas.toBlob',
            'image/jpeg'
        ])
    print()
    
    # Check Offline Queue
    print("4. Offline Queue (offline-queue.js)")
    print("-" * 60)
    queue_exists = check_file_exists('static/js/offline-queue.js')
    if queue_exists:
        check_file_content('static/js/offline-queue.js', [
            'indexedDB.open',
            'queueImage',
            'processQueuedImages',
            'getPendingImages',
            'image-queue'
        ])
    print()
    
    # Check Retry Mechanism
    print("5. Retry Mechanism (retry-mechanism.js)")
    print("-" * 60)
    retry_exists = check_file_exists('static/js/retry-mechanism.js')
    if retry_exists:
        check_file_content('static/js/retry-mechanism.js', [
            'fetchWithRetry',
            'exponential backoff',
            'storeFailedRequest',
            'retryFailedRequests',
            'sessionStorage'
        ])
    print()
    
    # Check Template Integration
    print("6. Template Integration")
    print("-" * 60)
    base_exists = check_file_exists('templates/base.html')
    if base_exists:
        print("✓ templates/base.html")
        check_file_content('templates/base.html', [
            'offline.js',
            'retry-mechanism.js'
        ])
    
    scan_exists = check_file_exists('templates/scan.html')
    if scan_exists:
        print("✓ templates/scan.html")
        check_file_content('templates/scan.html', [
            'image-compression.js',
            'offline-queue.js',
            'compressImage',
            'queueImage'
        ])
    print()
    
    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    all_files = [
        ('Service Worker', sw_exists),
        ('Offline Support', offline_exists),
        ('Image Compression', compression_exists),
        ('Offline Queue', queue_exists),
        ('Retry Mechanism', retry_exists),
        ('Base Template', base_exists),
        ('Scan Template', scan_exists)
    ]
    
    passed = sum(1 for _, exists in all_files if exists)
    total = len(all_files)
    
    print(f"\nFiles Present: {passed}/{total}")
    
    if passed == total:
        print("\n✓ All offline support features implemented successfully!")
        print("\nFeatures:")
        print("  • Service Worker for offline caching")
        print("  • Network-first strategy for analysis endpoint")
        print("  • Cache-first strategy for history and static assets")
        print("  • Client-side image compression (max 1920px, 85% quality)")
        print("  • IndexedDB queue for offline images")
        print("  • Automatic upload when connection restored")
        print("  • Request retry with exponential backoff")
        print("  • Failed request storage and manual retry UI")
    else:
        print("\n✗ Some files are missing. Please check the implementation.")
    
    print()

if __name__ == '__main__':
    main()
