# Design Document

## Overview

The AGBOT AI Pest Detection System is a modular, distributed web application that leverages deep learning to identify crop pests from leaf images and provides Integrated Pest Management (IPM) recommendations. The system architecture separates concerns across a Flask backend API, a Python-based AI inference microservice, a hybrid database system (PostgreSQL + MongoDB), and a responsive web frontend. This design ensures real-time performance (< 3 seconds per analysis), high accuracy (> 95%), scalability to thousands of concurrent users, and continuous improvement through farmer feedback.

The core innovation is the Damage-to-Insect Causality Engine, which uses an ensemble of EfficientNet-B0 (primary) and ResNet-50 (fallback) models to achieve robust pest identification. The system prioritizes sustainability by implementing an IPM recommendation engine that ranks cultural and biological controls above chemical pesticides, with region-specific regulatory filtering.

## Architecture

### High-Level System Architecture

The AGBOT system follows a microservices architecture with the following components:

```
┌─────────────────┐
│  Web Frontend   │ (HTML/CSS/JS + Service Workers)
│  (Mobile/Desktop)│
└────────┬────────┘
         │ HTTPS/WebSocket
         ▼
┌─────────────────┐
│  Flask Backend  │ (Python Flask API)
│  - Auth & Session│
│  - Business Logic│
│  - WebSocket Hub │
└────┬────────┬───┘
     │        │
     │        └──────────────┐
     │                       │
     ▼                       ▼
┌─────────────────┐   ┌──────────────────┐
│ AI Microservice │   │ Hybrid Database  │
│ (Python/FastAPI)│   │ - PostgreSQL     │
│ - EfficientNet  │   │ - MongoDB        │
│ - ResNet-50     │   │                  │
│ - OpenCV        │   │                  │
└─────────────────┘   └──────────────────┘
```

**Component Responsibilities:**

1. **Web Frontend**: Responsive UI for image capture/upload, result display, history viewing, and settings. Implements offline-first capabilities with Service Workers and client-side image compression.

2. **Flask Backend**: Primary API gateway handling authentication (JWT), user management, scan orchestration, IPM recommendation logic, and WebSocket connections for real-time alerts.

3. **AI Microservice**: Isolated Python service (FastAPI) dedicated to computationally intensive tasks: image preprocessing with OpenCV, model inference with EfficientNet-B0/ResNet-50, and confidence-based ensemble logic.

4. **Hybrid Database**:
   - **PostgreSQL**: Stores structured data (users, pests, treatments, IPM rules, scan records) with ACID guarantees and complex query support
   - **MongoDB**: Stores semi-structured data (detailed scan metadata, feedback annotations, analytics aggregations) with flexible schema

**Communication Patterns:**
- Frontend ↔ Backend: RESTful HTTP(S) for API calls, WebSocket for push notifications
- Backend ↔ AI Service: Internal REST API calls (or gRPC for efficiency)
- Backend ↔ Databases: Direct connections with connection pooling

**Deployment Strategy:**
- Containerized with Docker for all services
- Orchestrated with Kubernetes for auto-scaling
- Deployed on cloud infrastructure (AWS/Azure/GCP) with multi-region support
- GPU-enabled instances for AI microservice (AWS EC2 with NVIDIA GPUs or SageMaker)
- CDN for static assets and frequent responses

## Components and Interfaces

### 1. Image Upload and Validation Component

**Purpose**: Handle image acquisition from farmers via camera capture or file upload, validate format and size, and prepare for analysis.

**Interfaces**:
- **Input**: Multipart form data or base64-encoded image from frontend
- **Output**: Validated image file path or error message

**Implementation Details**:
- Supported formats: PNG, JPG, JPEG, GIF, WEBP
- Maximum file size: 10 MB (configurable)
- Client-side compression before upload to reduce bandwidth
- Server-side validation using file extension and MIME type checking
- Secure filename generation with timestamp prefix
- Storage in `static/uploads/` directory with unique naming

**API Endpoint**: `POST /api/scan/upload`

### 2. Image Preprocessing Pipeline

**Purpose**: Normalize and enhance images before feeding to AI models to improve inference accuracy.

**Interfaces**:
- **Input**: Raw image file path
- **Output**: Preprocessed 224×224 normalized tensor

**Processing Steps**:
1. Load image with OpenCV
2. Correct orientation using EXIF metadata
3. Optional: Detect and crop to leaf region using contour detection
4. Convert to HSV color space
5. Apply histogram equalization on V channel for lighting normalization
6. Convert back to BGR
7. Resize to 224×224 pixels
8. Normalize pixel values to [0, 1] range
9. Convert to tensor format for model input

**Performance Target**: < 100ms per image

### 3. Damage-to-Insect Causality Engine (AI Core)

**Purpose**: Identify pest species from preprocessed leaf images using ensemble deep learning models.

**Model Architecture**:
- **Primary Model**: EfficientNet-B0 (quantized to INT8)
  - Input: 224×224×3 RGB image
  - Output: Probability distribution over pest classes
  - Inference time: ~1-2 seconds on GPU
  - Model size: 13 MB
  - Accuracy: ~99.7% on training dataset

- **Fallback Model**: ResNet-50
  - Used when EfficientNet confidence < 85%
  - Provides complementary feature analysis
  - Inference time: ~2-3 seconds on GPU

**Ensemble Logic**:
```python
def identify_pest(image_tensor):
    # Primary inference
    primary_pred = efficientnet_model.predict(image_tensor)
    pest_label, confidence = get_top_prediction(primary_pred)
    
    # Fallback if low confidence
    if confidence < 0.85:
        fallback_pred = resnet_model.predict(image_tensor)
        alt_label, alt_conf = get_top_prediction(fallback_pred)
        
        if alt_conf > confidence:
            pest_label, confidence = alt_label, alt_conf
    
    return pest_label, confidence, get_alternatives(primary_pred, n=3)
```

**Interfaces**:
- **Input**: Preprocessed image tensor
- **Output**: JSON with pest_label, confidence, alternatives list
- **API Endpoint**: `POST /ai/detect` (internal)

### 4. IPM Recommendation Engine

**Purpose**: Generate prioritized, region-specific treatment recommendations following IPM principles.

**Architecture**: Three-layer hybrid system

**Layer 1: Rule-Based Core**
- Knowledge base of IF-THEN rules encoding expert IPM guidelines
- Rules stored in PostgreSQL `IPM_REC` table
- Structure: `(pest_id, treatment_id, priority, region, conditions)`
- Example rule: "IF pest=Fall_Armyworm AND crop=Corn AND region=East_Africa THEN recommend parasitic_wasp_release (priority=primary)"

**Layer 2: AI Ranking**
- Machine learning model (collaborative filtering) that learns from historical treatment outcomes
- Inputs: pest, region, crop, farmer profile, historical success rates
- Output: Ranked list of treatments with predicted success probability
- Initially uses rule-based priorities; improves as data accumulates

**Layer 3: Regulatory Filter**
- Cross-references recommendations with regional pesticide regulations
- Filters out prohibited treatments
- Annotates restricted treatments with warnings
- Integrates with external databases (USDA IPM, local ag ministry APIs)

**Recommendation Flow**:
```python
def get_recommendations(pest, crop, region, farmer_profile):
    # Step 1: Query rule base
    rule_suggestions = query_ipm_rules(pest, crop, region)
    
    # Step 2: AI ranking (if model trained)
    if ml_model_available():
        ranked_list = ml_model.rank(rule_suggestions, farmer_profile)
    else:
        ranked_list = sort_by_priority(rule_suggestions)
    
    # Step 3: Regulatory filtering
    final_list = []
    for rec in ranked_list:
        if is_approved(rec, region):
            final_list.append(rec)
        else:
            rec.note = "Not approved in your region"
    
    return final_list
```

**Interfaces**:
- **Input**: Pest ID, crop type, region, farmer profile
- **Output**: Ordered list of treatment recommendations with descriptions, categories, and notes
- **API Endpoint**: `GET /api/recommendations/{pest_id}`

### 5. Feedback Collection and Storage

**Purpose**: Capture farmer corrections to improve model accuracy over time.

**Interfaces**:
- **Input**: Detection ID, is_correct (boolean), actual_pest_name (if incorrect), notes
- **Output**: Confirmation message and updated detection status

**Storage Strategy**:
- **PostgreSQL**: Update `DETECTION` table status field to "corrected"
- **MongoDB**: Store detailed feedback in `FEEDBACK` collection with full context
- **Training Repository**: Flag corrected images for inclusion in next retraining batch

**Feedback Triggers**:
- Automatic prompt when confidence < 75%
- Manual feedback button always available on results page
- Periodic follow-up requests for high-impact detections

**API Endpoint**: `POST /api/feedback`

### 6. Scan History and Analytics

**Purpose**: Provide farmers with historical view of their scans and enable system-wide analytics.

**User History**:
- Query PostgreSQL `DETECTION` table filtered by user_id
- Join with `PEST` table for pest details
- Display chronologically with filters (date range, pest type, severity)
- Export functionality to JSON/CSV

**System Analytics**:
- MongoDB aggregation pipeline for pest occurrence by region/time
- Precomputed summaries in `ANALYTICS` collection
- Outbreak detection: Alert when occurrences exceed 1.5× historical average
- Visualization data for heatmaps and trend charts

**API Endpoints**:
- `GET /api/history` - User's scan history
- `GET /api/analytics/trends` - System-wide pest trends
- `GET /api/analytics/outbreaks` - Active outbreak alerts

### 7. Multi-Language Support

**Purpose**: Deliver localized content in English, Spanish, Hindi, and Swahili.

**Implementation**:
- Translation files: `translations/{lang}.json` with nested key-value structure
- Backend: Flask context processor injects translations into templates
- Database: Pest names stored with multilingual columns (`name_en`, `name_es`, `name_hi`, `name_sw`)
- Frontend: JavaScript i18n library for dynamic content
- Fallback: English used when translation missing, with logging for future addition

**Language Detection**:
1. Check user profile language preference (if authenticated)
2. Check session language setting
3. Check browser `Accept-Language` header
4. Default to English

## Data Models

### PostgreSQL Schema

**USER Table**
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(120) UNIQUE NOT NULL,
    phone VARCHAR(20) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    location VARCHAR(100),
    language VARCHAR(10) DEFAULT 'en',
    units VARCHAR(10) DEFAULT 'metric',
    theme VARCHAR(20) DEFAULT 'emerald',
    farm_name VARCHAR(100),
    farm_size VARCHAR(50),
    crops TEXT,
    notification_email BOOLEAN DEFAULT TRUE,
    notification_push BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    oauth_provider VARCHAR(50),
    oauth_id VARCHAR(255)
);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_location ON users(location);
```

**PEST Table**
```sql
CREATE TABLE pests (
    id SERIAL PRIMARY KEY,
    common_name VARCHAR(100) NOT NULL,
    scientific_name VARCHAR(100),
    category VARCHAR(50),  -- insect, fungus, disease
    description TEXT,
    name_es VARCHAR(100),
    name_hi VARCHAR(100),
    name_sw VARCHAR(100)
);
CREATE INDEX idx_pests_common_name ON pests(common_name);
CREATE INDEX idx_pests_category ON pests(category);
```

**TREATMENT Table**
```sql
CREATE TABLE treatments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    type VARCHAR(50) NOT NULL,  -- cultural, biological, chemical
    description TEXT,
    description_es TEXT,
    description_hi TEXT,
    description_sw TEXT,
    cost_estimate VARCHAR(50),
    effectiveness_rate FLOAT
);
```

**IPM_REC Table**
```sql
CREATE TABLE ipm_recommendations (
    id SERIAL PRIMARY KEY,
    pest_id INTEGER REFERENCES pests(id),
    treatment_id INTEGER REFERENCES treatments(id),
    priority VARCHAR(20),  -- primary, secondary, last_resort
    region VARCHAR(50),  -- region code or 'global'
    crop_type VARCHAR(50),
    conditions TEXT,  -- JSON string with additional conditions
    success_rate FLOAT
);
CREATE INDEX idx_ipm_pest ON ipm_recommendations(pest_id);
CREATE INDEX idx_ipm_region ON ipm_recommendations(region);
```

**DETECTION Table**
```sql
CREATE TABLE scans (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    image_path VARCHAR(255),
    pest_identified VARCHAR(100),
    pest_scientific VARCHAR(100),
    confidence FLOAT,
    status VARCHAR(50),  -- identified, corrected, verified
    severity VARCHAR(50),  -- mild, moderate, severe, healthy
    crop_type VARCHAR(100),
    field_name VARCHAR(100),
    damage_pattern TEXT,
    model_version VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_scans_user ON scans(user_id);
CREATE INDEX idx_scans_created ON scans(created_at);
CREATE INDEX idx_scans_pest ON scans(pest_identified);
```

**FEEDBACK Table**
```sql
CREATE TABLE feedbacks (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    scan_id INTEGER REFERENCES scans(id) NOT NULL,
    is_correct BOOLEAN NOT NULL,
    actual_pest_name VARCHAR(100),
    actual_pest_scientific VARCHAR(100),
    notes TEXT,
    helpful BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_feedbacks_scan ON feedbacks(scan_id);
```

### MongoDB Schema

**detection_meta Collection**
```json
{
    "_id": "detection_12345",
    "user_id": 42,
    "pest_label": "Tomato Leafminer",
    "confidence": 0.92,
    "alternatives": [
        {"label": "Tomato Hornworm", "confidence": 0.07},
        {"label": "Whitefly", "confidence": 0.01}
    ],
    "image_info": {
        "filename": "20251125_143022_leaf.jpg",
        "resolution": "1920x1080",
        "file_size_kb": 2048,
        "exif_data": {...}
    },
    "model_details": {
        "primary_model": "EfficientNet-B0",
        "primary_version": "v2.1.0",
        "fallback_used": false,
        "preprocessing_time_ms": 87,
        "inference_time_ms": 1543,
        "total_time_ms": 1630
    },
    "location": {
        "type": "Point",
        "coordinates": [-95.7129, 37.0902]
    },
    "timestamp": "2025-11-25T14:30:45Z"
}
```

**feedback Collection**
```json
{
    "_id": "feedback_67890",
    "detection_id": "detection_12345",
    "user_id": 42,
    "is_correct": false,
    "corrected_label": "Tomato Hornworm",
    "confidence_in_correction": "high",
    "comments": "The pest has a horn-like protrusion",
    "feedback_time": "2025-11-25T15:00:00Z",
    "image_flagged_for_retraining": true
}
```

**analytics Collection**
```json
{
    "_id": "analytics_region_202511",
    "region": "East_Africa",
    "month": "2025-11",
    "pest_occurrences": {
        "Fall_Armyworm": 234,
        "Aphids": 156,
        "Whitefly": 89
    },
    "total_scans": 512,
    "outbreak_alerts": [
        {
            "pest": "Fall_Armyworm",
            "threshold_exceeded": 1.8,
            "alert_issued": "2025-11-20T10:00:00Z"
        }
    ],
    "last_updated": "2025-11-25T23:59:59Z"
}
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Image Upload and Validation Properties

Property 1: File format validation
*For any* file submitted for upload, if the file extension is one of PNG, JPG, JPEG, GIF, or WEBP (case-insensitive), then the validation should pass; otherwise it should fail with an error message listing supported formats
**Validates: Requirements 1.2, 1.3**

Property 2: Invalid format rejection
*For any* file with an unsupported extension, the system should reject the upload and return an error message containing the list of supported formats
**Validates: Requirements 1.3**

Property 3: Valid image preview
*For any* valid image file that passes format validation, the system should generate and return a preview representation of that image
**Validates: Requirements 1.4**

Property 4: Analysis initiation
*For any* confirmed image, initiating analysis should trigger a loading state and begin the preprocessing pipeline
**Validates: Requirements 1.5**

### AI Inference and Performance Properties

Property 5: Preprocessing performance
*For any* image submitted for analysis, the preprocessing step (orientation correction, resizing, normalization) should complete in under 100 milliseconds
**Validates: Requirements 2.1**

Property 6: Primary model inference time
*For any* preprocessed image tensor, EfficientNet-B0 inference should return a prediction within 2 seconds
**Validates: Requirements 2.2**

Property 7: Fallback model invocation
*For any* EfficientNet-B0 prediction with confidence score below 85%, the system should invoke ResNet-50 for a second prediction
**Validates: Requirements 2.3**

Property 8: Highest confidence selection
*For any* pair of predictions from EfficientNet-B0 and ResNet-50, the system should select the prediction with the higher confidence score as the final result
**Validates: Requirements 2.4**

Property 9: Complete analysis response
*For any* completed analysis, the response should contain pest_name, scientific_name, and confidence_percentage fields
**Validates: Requirements 3.1**

Property 10: Confidence level classification
*For any* confidence score, the system should classify it as "High Confidence" (≥85%), "Moderate Confidence" (70-84%), or "Low Confidence" (<70%) according to the defined thresholds
**Validates: Requirements 3.2, 3.3, 3.4**

### IPM Recommendation Properties

Property 11: Recommendation retrieval
*For any* identified pest with a valid pest_id, the system should retrieve at least one treatment recommendation from the IPM engine
**Validates: Requirements 4.1**

Property 12: IPM priority ordering
*For any* set of treatment recommendations, cultural and biological treatments should appear before chemical treatments in the ordered list
**Validates: Requirements 4.2**

Property 13: Chemical treatment annotation
*For any* treatment recommendation with type="chemical", the recommendation should include a "Last Resort" label and safety warnings
**Validates: Requirements 4.3**

Property 14: Regional treatment filtering
*For any* region with defined regulations, prohibited treatments for that region should not appear in the final recommendation list
**Validates: Requirements 4.4**

### Feedback and Data Persistence Properties

Property 15: Dual database persistence
*For any* feedback submission, a record should be created in both the PostgreSQL feedbacks table and the MongoDB feedback collection with matching detection_id
**Validates: Requirements 5.3**

Property 16: Feedback confirmation
*For any* successfully saved feedback, the system should return a success message and update the detection record status to "corrected"
**Validates: Requirements 5.4**

Property 17: Proactive feedback request
*For any* analysis result with confidence score below 75%, the feedback prompt should be displayed prominently before navigation
**Validates: Requirements 5.5**

### History and Export Properties

Property 18: User scan retrieval
*For any* authenticated farmer accessing the history page, the system should retrieve all scans where user_id matches the farmer's ID
**Validates: Requirements 6.1**

Property 19: History field completeness
*For any* scan displayed in history, the display should include date, pest_identified, confidence, and severity fields
**Validates: Requirements 6.2**

Property 20: Historical detail retrieval
*For any* historical scan selected by a farmer, the system should retrieve and display the complete scan record including image_path and associated recommendations
**Validates: Requirements 6.3**

Property 21: Export format validity
*For any* history export request, the generated file should be valid JSON or CSV format and parseable by standard libraries
**Validates: Requirements 6.4**

### Localization Properties

Property 22: Browser language detection
*For any* first-time visitor, the system should parse the Accept-Language header and set the interface language to the best match from supported languages (en, es, hi, sw)
**Validates: Requirements 7.1**

Property 23: Language switch completeness
*For any* language change action, all UI text elements, pest names, and treatment descriptions should update to the selected language
**Validates: Requirements 7.2**

Property 24: Pest name localization
*For any* pest displayed to a farmer, the system should show the localized name field corresponding to the farmer's language preference (name_en, name_es, name_hi, or name_sw)
**Validates: Requirements 7.3**

Property 25: Translation fallback
*For any* missing translation key in a non-English language, the system should display the English translation and log the missing key
**Validates: Requirements 7.5**

### Mobile and Offline Properties

Property 26: Responsive interface
*For any* mobile device screen width (< 768px), the interface should render with mobile-optimized layout and touch-friendly controls
**Validates: Requirements 8.1**

Property 27: Offline page caching
*For any* page viewed while online, the Service Worker should cache the page assets so they are available when offline
**Validates: Requirements 8.2**

Property 28: Offline image queuing
*For any* image captured while offline, the system should add it to an upload queue and automatically upload when connectivity is restored
**Validates: Requirements 8.3**

Property 29: Client-side compression
*For any* image uploaded, the client should compress it before transmission, resulting in a smaller file size than the original
**Validates: Requirements 8.4**

Property 30: Request retry availability
*For any* failed network request, the system should display a retry button and cache the request parameters for automatic retry
**Validates: Requirements 8.5**

### Model Improvement Properties

Property 31: Feedback aggregation
*For any* submitted feedback, the system should add the corrected image and label to the training dataset repository
**Validates: Requirements 9.1**

Property 32: Retraining threshold trigger
*For any* pest type, when the count of feedback corrections reaches 100, the system should trigger a model retraining notification
**Validates: Requirements 9.2**

Property 33: Model accuracy validation
*For any* newly trained model, it should achieve at least 95% accuracy on the held-out test set before being marked as deployable
**Validates: Requirements 9.3**

Property 34: Model version logging
*For any* detection performed, the system should record the model_version field in the detection record
**Validates: Requirements 9.4**

### Scalability and Performance Properties

Property 35: Auto-scaling up
*For any* measurement period where system load exceeds 80% of capacity, the system should provision additional server instances
**Validates: Requirements 10.1**

Property 36: Auto-scaling down
*For any* 10-minute period where system load remains below 30% of capacity, the system should scale down server instances
**Validates: Requirements 10.2**

Property 37: Request queuing
*For any* set of concurrent AI inference requests, the system should queue them and process each with GPU-enabled instances
**Validates: Requirements 10.3**

Property 38: Performance warning logging
*For any* database query with latency exceeding 500 milliseconds, the system should log a performance warning
**Validates: Requirements 10.4**

### Security Properties

Property 39: Password hashing
*For any* new user account creation, the password should be hashed using Argon2 before storage, and the plaintext password should never be stored
**Validates: Requirements 11.1**

Property 40: JWT token issuance
*For any* successful login, the system should issue a JWT token with an expiration timestamp exactly 24 hours in the future
**Validates: Requirements 11.2**

Property 41: HTTPS enforcement
*For any* HTTP request to the API, the system should enforce HTTPS with TLS 1.2 or higher
**Validates: Requirements 11.3**

Property 42: Image encryption at rest
*For any* uploaded image stored to disk, the file should be encrypted using AES-256 before writing
**Validates: Requirements 11.4**

Property 43: Data deletion compliance
*For any* account deletion request, all personal data associated with the user_id should be removed from all databases within 30 days
**Validates: Requirements 11.5**

### Analytics Properties

Property 44: Location-based aggregation
*For any* detection record with location data, the system should extract the region and increment the pest occurrence count for that region in the analytics collection
**Validates: Requirements 12.1**

Property 45: Trend query grouping
*For any* pest trend query, the results should be grouped by pest_type, region, and time_period as specified in the query parameters
**Validates: Requirements 12.2**

Property 46: Outbreak alert generation
*For any* region and pest combination, when current occurrences exceed 1.5× the historical average, the system should generate an outbreak alert
**Validates: Requirements 12.3**

Property 47: WebSocket alert delivery
*For any* generated outbreak alert, the system should send a WebSocket push notification to all farmers in the affected region
**Validates: Requirements 12.4**

## Error Handling

### Client-Side Error Handling

**Image Upload Errors**:
- Invalid file format: Display user-friendly message with supported formats
- File too large (>10MB): Prompt to compress or select smaller image
- Network failure during upload: Show retry button and queue for automatic retry
- Camera access denied: Display instructions to enable camera permissions

**Analysis Errors**:
- Timeout (>3 seconds): "Analysis taking longer than expected. Please try again."
- AI service unavailable: "Service temporarily unavailable. Please try again in a few moments."
- Unable to identify (<50% confidence): "Unable to identify pest. Please ensure the image is clear and try again."

**Authentication Errors**:
- Invalid credentials: "Incorrect email or password"
- Expired JWT: Automatically redirect to login with message "Session expired. Please log in again."
- Account locked: "Account temporarily locked due to multiple failed attempts. Try again in 15 minutes."

### Server-Side Error Handling

**Database Errors**:
- Connection failure: Retry with exponential backoff (3 attempts), then return 503 Service Unavailable
- Query timeout: Log warning, optimize query, return cached data if available
- Constraint violation: Return 400 Bad Request with specific error message

**AI Service Errors**:
- Model loading failure: Log critical error, alert ops team, return fallback response
- GPU out of memory: Queue request for retry, scale up GPU instances
- Inference exception: Log error with image metadata, return "Unable to process image" to user

**External API Errors**:
- Regulatory database unavailable: Use cached regulations, add note "Using cached data"
- Weather API timeout: Skip weather data, continue with core functionality
- OAuth provider error: Fall back to email/password login

### Error Logging and Monitoring

All errors are logged with:
- Timestamp
- User ID (if authenticated)
- Request ID for tracing
- Error type and message
- Stack trace (for server errors)
- Context data (image metadata, model version, etc.)

Critical errors trigger alerts to operations team via:
- PagerDuty for production incidents
- Slack notifications for warnings
- Email digest for non-urgent issues

## Testing Strategy

### Unit Testing

**Framework**: pytest for Python backend, Jest for JavaScript frontend

**Coverage Targets**:
- Core business logic: 90% code coverage
- API endpoints: 100% coverage
- Database models: 85% coverage
- Utility functions: 95% coverage

**Key Unit Test Areas**:
1. **Image validation**: Test file format checking, size limits, MIME type validation
2. **Preprocessing functions**: Test orientation correction, resizing, normalization
3. **Confidence classification**: Test threshold logic for High/Moderate/Low confidence
4. **IPM recommendation ordering**: Test sorting logic for cultural/biological/chemical priority
5. **Regional filtering**: Test treatment filtering based on region regulations
6. **JWT token generation**: Test token creation, expiration, validation
7. **Password hashing**: Test Argon2 hashing and verification
8. **Language detection**: Test Accept-Language header parsing
9. **Translation fallback**: Test English fallback for missing translations
10. **Database CRUD operations**: Test create, read, update, delete for all models

### Property-Based Testing

**Framework**: Hypothesis for Python

**Configuration**: Each property test runs a minimum of 100 iterations with randomly generated inputs

**Test Tagging**: Each property-based test includes a comment with the format:
```python
# Feature: ai-pest-detection, Property X: [property description]
```

**Key Property Test Areas**:

1. **File format validation** (Property 1):
   - Generate random filenames with various extensions
   - Verify only supported formats pass validation

2. **Preprocessing performance** (Property 5):
   - Generate random images of various sizes
   - Measure preprocessing time, assert < 100ms

3. **Confidence selection** (Property 8):
   - Generate random pairs of confidence scores
   - Verify higher confidence is always selected

4. **IPM ordering** (Property 12):
   - Generate random treatment lists with mixed types
   - Verify cultural/biological always precede chemical

5. **Dual database persistence** (Property 15):
   - Generate random feedback data
   - Verify records exist in both PostgreSQL and MongoDB

6. **Language fallback** (Property 25):
   - Generate random translation keys
   - Verify English fallback for missing translations

7. **Password hashing** (Property 39):
   - Generate random passwords
   - Verify Argon2 hash is created and plaintext is not stored

8. **Outbreak detection** (Property 46):
   - Generate random occurrence data
   - Verify alert triggers when threshold exceeded

### Integration Testing

**Scope**: Test interactions between components

**Key Integration Tests**:
1. **End-to-end image analysis flow**: Upload → Preprocess → Inference → Recommendations → Storage
2. **Feedback loop**: Submit feedback → Store in databases → Flag for retraining
3. **Authentication flow**: Register → Login → JWT issuance → Protected endpoint access
4. **Multi-language flow**: Change language → Fetch translations → Update UI → Persist preference
5. **Offline-online sync**: Capture offline → Queue → Restore connectivity → Upload → Process
6. **Outbreak alert flow**: Detect threshold → Generate alert → Send WebSocket → Farmer receives notification

### Performance Testing

**Tools**: Locust for load testing, pytest-benchmark for micro-benchmarks

**Performance Targets**:
- Image preprocessing: < 100ms (Property 5)
- Model inference: < 2 seconds (Property 6)
- Total analysis time: < 3 seconds (Requirement 2)
- Database queries: < 500ms (Requirement 10.4)
- API response time (non-AI): < 200ms

**Load Testing Scenarios**:
1. Concurrent image uploads: 1000 simultaneous users
2. Sustained load: 500 requests/second for 10 minutes
3. Spike test: 0 → 2000 users in 30 seconds
4. Stress test: Gradually increase load until system degrades

### Security Testing

**Areas**:
1. **Authentication**: Test JWT expiration, token tampering, brute force protection
2. **Authorization**: Test access control for user-specific resources
3. **Input validation**: Test SQL injection, XSS, file upload exploits
4. **Encryption**: Verify HTTPS enforcement, password hashing, data encryption at rest
5. **GDPR compliance**: Test data deletion, export, consent management

### Model Testing

**Accuracy Testing**:
- Held-out test set: 95% accuracy minimum (Property 33)
- Per-class accuracy: No class below 85%
- Confusion matrix analysis for common misclassifications

**Robustness Testing**:
- Test with various image qualities (blurry, low-light, high-glare)
- Test with edge cases (multiple pests, no pest, non-leaf images)
- Test with images from different regions and crops

**Fairness Testing**:
- Ensure accuracy is consistent across regions
- Verify no bias toward specific crops or pest types

## Deployment Architecture

### Infrastructure

**Cloud Provider**: AWS (primary), with multi-region deployment

**Compute**:
- Flask Backend: AWS ECS (Fargate) with auto-scaling
- AI Microservice: AWS EC2 with NVIDIA GPUs (p3.2xlarge instances)
- Load Balancer: AWS Application Load Balancer with SSL termination

**Storage**:
- PostgreSQL: AWS RDS (Multi-AZ deployment)
- MongoDB: MongoDB Atlas (M30 cluster)
- Image Storage: AWS S3 with encryption at rest
- Cache: AWS ElastiCache (Redis) for session data and frequent queries

**Networking**:
- VPC with public and private subnets
- Security groups restricting access between components
- CloudFront CDN for static assets and API caching

### CI/CD Pipeline

**Version Control**: Git with GitHub

**Pipeline Stages**:
1. **Commit**: Developer pushes code to feature branch
2. **Build**: GitHub Actions builds Docker images
3. **Test**: Run unit tests, property tests, integration tests
4. **Security Scan**: Snyk for dependency vulnerabilities, SonarQube for code quality
5. **Staging Deploy**: Deploy to staging environment
6. **Smoke Tests**: Run critical path tests on staging
7. **Production Deploy**: Blue-green deployment to production
8. **Monitoring**: Verify health checks, monitor error rates

**Deployment Strategy**: Blue-green deployment with automatic rollback on health check failure

### Monitoring and Observability

**Metrics** (CloudWatch):
- Request rate, error rate, latency (p50, p95, p99)
- AI inference time, model confidence distribution
- Database query performance, connection pool usage
- Auto-scaling events, instance health

**Logging** (CloudWatch Logs):
- Application logs (INFO, WARNING, ERROR, CRITICAL)
- Access logs (all API requests)
- Audit logs (authentication, data access, modifications)

**Tracing** (AWS X-Ray):
- End-to-end request tracing
- Service dependency mapping
- Performance bottleneck identification

**Alerting** (PagerDuty + Slack):
- Critical: System down, database unavailable, AI service failure
- Warning: High error rate, slow queries, low disk space
- Info: Deployment completed, auto-scaling event

### Disaster Recovery

**Backup Strategy**:
- PostgreSQL: Automated daily backups with 30-day retention
- MongoDB: Continuous backup with point-in-time recovery
- S3 images: Cross-region replication to secondary region

**Recovery Objectives**:
- RTO (Recovery Time Objective): 1 hour
- RPO (Recovery Point Objective): 15 minutes

**Failover Plan**:
1. Detect failure via health checks
2. Route traffic to secondary region
3. Restore databases from latest backup
4. Verify system functionality
5. Notify operations team

## Future Enhancements

1. **Mobile Native Apps**: React Native apps for iOS and Android with enhanced offline capabilities
2. **Voice Interface**: Voice-based pest reporting and recommendation playback for low-literacy users
3. **Drone Integration**: Analyze aerial crop images for large-scale pest detection
4. **Weather Integration**: Correlate pest outbreaks with weather patterns for predictive alerts
5. **Community Features**: Farmer forums, expert Q&A, peer-to-peer knowledge sharing
6. **Precision Agriculture**: Integration with IoT sensors for soil, moisture, and temperature data
7. **Blockchain Traceability**: Immutable record of pest treatments for organic certification
8. **AR Visualization**: Augmented reality overlay showing pest information when camera points at leaf
9. **Marketplace Integration**: Connect farmers with IPM product suppliers and agricultural extension services
10. **Advanced Analytics**: Machine learning models for yield prediction, optimal treatment timing, and cost-benefit analysis
