# History API Endpoints Guide

## Overview
This guide provides examples for using the scan history and export API endpoints.

## Authentication
All endpoints require authentication. Include session cookies or JWT token in requests.

## Endpoints

### 1. Get Scan History

**Endpoint**: `GET /api/history`

**Description**: Retrieve all scans for the authenticated user, ordered by most recent first.

**Request**:
```bash
curl -X GET http://localhost:5001/api/history \
  -H "Cookie: session=<your-session-cookie>"
```

**Response** (200 OK):
```json
[
  {
    "id": 123,
    "date": "2025-11-25T14:30:45.123456",
    "pest_identified": "Japanese Beetle",
    "pest_scientific": "Popillia japonica",
    "confidence": 92.5,
    "severity": "moderate",
    "status": "identified",
    "crop_type": "corn",
    "field_name": "Field A"
  },
  {
    "id": 122,
    "date": "2025-11-24T10:15:30.654321",
    "pest_identified": "Aphids",
    "pest_scientific": "Aphidoidea",
    "confidence": 87.3,
    "severity": "mild",
    "status": "corrected",
    "crop_type": "tomato",
    "field_name": "Field B"
  }
]
```

**Use Cases**:
- Display scan history in user dashboard
- Show recent detections
- Track pest occurrences over time

---

### 2. Get Scan Detail

**Endpoint**: `GET /api/history/<scan_id>`

**Description**: Retrieve detailed information for a specific scan, including MongoDB metadata and IPM recommendations.

**Request**:
```bash
curl -X GET http://localhost:5001/api/history/123 \
  -H "Cookie: session=<your-session-cookie>"
```

**Response** (200 OK):
```json
{
  "id": 123,
  "date": "2025-11-25T14:30:45.123456",
  "pest_identified": "Japanese Beetle",
  "pest_scientific": "Popillia japonica",
  "confidence": 92.5,
  "severity": "moderate",
  "status": "identified",
  "crop_type": "corn",
  "field_name": "Field A",
  "damage_pattern": "Skeletonized leaves",
  "model_version": "v2.1.0",
  "image_path": "static/uploads/20251125_143045_leaf.jpg",
  "metadata": {
    "alternatives": [
      {
        "label": "Rose Chafer",
        "confidence": 0.05
      },
      {
        "label": "June Beetle",
        "confidence": 0.02
      }
    ],
    "image_info": {
      "filename": "20251125_143045_leaf.jpg",
      "file_size_kb": 2048
    },
    "model_details": {
      "primary_model": "EfficientNet-B0",
      "primary_version": "v2.1.0",
      "fallback_used": false,
      "preprocessing_time_ms": 87,
      "inference_time_ms": 1543,
      "total_time_ms": 1630
    },
    "location": {},
    "flagged_for_retraining": false
  },
  "recommendations": [
    {
      "id": 1,
      "treatment_name": "Hand-picking",
      "type": "cultural",
      "description": "Remove beetles by hand in early morning when they are less active",
      "priority": "primary",
      "cost_estimate": "Low",
      "effectiveness_rate": 0.75,
      "success_rate": 0.8,
      "is_last_resort": false,
      "safety_warning": null,
      "warning_icon": null,
      "regulatory_note": null
    },
    {
      "id": 2,
      "treatment_name": "Neem oil spray",
      "type": "biological",
      "description": "Apply neem oil following label instructions",
      "priority": "secondary",
      "cost_estimate": "Medium",
      "effectiveness_rate": 0.85,
      "success_rate": 0.82,
      "is_last_resort": false,
      "safety_warning": null,
      "warning_icon": null,
      "regulatory_note": null
    }
  ]
}
```

**Error Response** (404 Not Found):
```json
{
  "error": "Scan not found or access denied"
}
```

**Use Cases**:
- Display full scan details page
- Review past recommendations
- Analyze model performance
- Check alternative predictions

---

### 3. Export Scans (JSON)

**Endpoint**: `GET /api/export/scans?format=json`

**Description**: Export all user scans as a JSON file.

**Request**:
```bash
curl -X GET "http://localhost:5001/api/export/scans?format=json" \
  -H "Cookie: session=<your-session-cookie>" \
  -o scan_history.json
```

**Response Headers**:
```
Content-Type: application/json
Content-Disposition: attachment; filename=scan_history_20251125.json
```

**Response Body**: Array of scan objects (same structure as history endpoint)

**Use Cases**:
- Backup scan data
- Import into other systems
- Data analysis with custom tools
- Share data with agronomists

---

### 4. Export Scans (CSV)

**Endpoint**: `GET /api/export/scans?format=csv`

**Description**: Export all user scans as a CSV file.

**Request**:
```bash
curl -X GET "http://localhost:5001/api/export/scans?format=csv" \
  -H "Cookie: session=<your-session-cookie>" \
  -o scan_history.csv
```

**Response Headers**:
```
Content-Type: text/csv
Content-Disposition: attachment; filename=scan_history_20251125.csv
```

**Response Body**:
```csv
ID,Date,Pest Identified,Scientific Name,Confidence (%),Severity,Status,Crop Type,Field Name,Model Version
123,2025-11-25 14:30:45,Japanese Beetle,Popillia japonica,92.5,moderate,identified,corn,Field A,v2.1.0
122,2025-11-24 10:15:30,Aphids,Aphidoidea,87.3,mild,corrected,tomato,Field B,v2.1.0
```

**Use Cases**:
- Import into Excel/Google Sheets
- Generate reports
- Statistical analysis
- Record keeping

---

### 5. Export with Invalid Format

**Endpoint**: `GET /api/export/scans?format=xml`

**Description**: Attempting to export with an unsupported format returns an error.

**Response** (400 Bad Request):
```json
{
  "error": "Unsupported format. Use format=json or format=csv"
}
```

---

## Frontend Integration Examples

### JavaScript/Fetch API

#### Get History
```javascript
async function getHistory() {
  const response = await fetch('/api/history');
  const history = await response.json();
  
  // Display in UI
  history.forEach(scan => {
    console.log(`${scan.date}: ${scan.pest_identified} (${scan.confidence}%)`);
  });
}
```

#### Get Scan Detail
```javascript
async function getScanDetail(scanId) {
  const response = await fetch(`/api/history/${scanId}`);
  const detail = await response.json();
  
  // Display detailed information
  console.log('Pest:', detail.pest_identified);
  console.log('Recommendations:', detail.recommendations.length);
}
```

#### Export as JSON
```javascript
function exportJSON() {
  window.location.href = '/api/export/scans?format=json';
}
```

#### Export as CSV
```javascript
function exportCSV() {
  window.location.href = '/api/export/scans?format=csv';
}
```

### jQuery

```javascript
// Get history
$.get('/api/history', function(data) {
  $('#history-list').empty();
  data.forEach(function(scan) {
    $('#history-list').append(
      `<li>${scan.pest_identified} - ${scan.confidence}%</li>`
    );
  });
});

// Get scan detail
$.get('/api/history/123', function(data) {
  $('#scan-detail').html(`
    <h3>${data.pest_identified}</h3>
    <p>Confidence: ${data.confidence}%</p>
    <p>Recommendations: ${data.recommendations.length}</p>
  `);
});
```

---

## Error Handling

### Common Error Responses

**401 Unauthorized** - User not authenticated:
```json
{
  "error": "Authentication required"
}
```

**404 Not Found** - Scan doesn't exist or user doesn't have access:
```json
{
  "error": "Scan not found or access denied"
}
```

**500 Internal Server Error** - Server error:
```json
{
  "error": "Failed to retrieve scan history"
}
```

### Best Practices

1. **Always check response status** before parsing JSON
2. **Handle network errors** with try-catch or .catch()
3. **Show user-friendly messages** instead of raw error text
4. **Implement retry logic** for transient failures
5. **Cache history data** to reduce server load

---

## Performance Tips

1. **Pagination**: For users with many scans, consider implementing pagination
2. **Caching**: Cache history data on client side with reasonable TTL
3. **Lazy Loading**: Load scan details only when user clicks on a scan
4. **Debouncing**: Debounce search/filter operations
5. **Background Export**: For large exports, consider background processing

---

## Security Notes

1. All endpoints require authentication
2. Users can only access their own scans
3. Scan IDs are validated to prevent injection attacks
4. Export files include timestamp to prevent caching issues
5. HTTPS should be used in production

---

## Testing

Use the provided test scripts:

```bash
# Run unit tests
python -m pytest test_history_endpoints.py -v

# Run manual demo (requires Flask app running)
python demo_history_endpoints.py
```

---

## Support

For issues or questions:
1. Check server logs for detailed error messages
2. Verify authentication is working
3. Ensure database connections are active
4. Test with the demo script first
