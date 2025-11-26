# Implementation Plan

- [x] 1. Set up Python AI microservice infrastructure





  - Create FastAPI application structure for AI inference service
  - Set up Docker container with Python 3.9+, OpenCV, TensorFlow/PyTorch
  - Configure GPU support in Docker (NVIDIA runtime)
  - Implement health check endpoint `/health`
  - _Requirements: 2.1, 2.2_

- [x] 1.1 Implement image preprocessing pipeline


  - Create `preprocess_image()` function using OpenCV
  - Implement EXIF orientation correction
  - Add HSV color space conversion and histogram equalization
  - Implement resize to 224×224 and normalization to [0,1]
  - Return preprocessed tensor in model-ready format
  - _Requirements: 2.1_

- [ ]* 1.2 Write property test for preprocessing performance
  - **Property 5: Preprocessing performance**
  - **Validates: Requirements 2.1**

- [x] 1.3 Implement EfficientNet-B0 model loading and inference


  - Load pre-trained EfficientNet-B0 model (quantized INT8)
  - Create `predict_primary()` function that accepts tensor and returns (pest_label, confidence, alternatives)
  - Implement top-N prediction extraction (N=3 for alternatives)
  - Cache model in memory at service startup
  - _Requirements: 2.2_

- [ ]* 1.4 Write property test for primary model inference time
  - **Property 6: Primary model inference time**
  - **Validates: Requirements 2.2**

- [x] 1.5 Implement ResNet-50 fallback model


  - Load pre-trained ResNet-50 model
  - Create `predict_fallback()` function with same interface as primary
  - Implement ensemble logic: invoke fallback only if primary confidence < 85%
  - Select prediction with highest confidence between primary and fallback
  - _Requirements: 2.3, 2.4_

- [ ]* 1.6 Write property tests for fallback logic
  - **Property 7: Fallback model invocation**
  - **Property 8: Highest confidence selection**
  - **Validates: Requirements 2.3, 2.4**

- [x] 1.7 Create AI service API endpoint


  - Implement `POST /ai/detect` endpoint in FastAPI
  - Accept image file in multipart form data
  - Call preprocessing → primary inference → (optional) fallback
  - Return JSON: `{pest_label, scientific_name, confidence, alternatives, processing_time_ms}`
  - Return 408 Timeout if internal processing exceeds 2.8 seconds (allowing 200ms buffer for network)
  - _Requirements: 2.2, 2.5, 3.1_

- [ ]* 1.8 Write property test for complete analysis response
  - **Property 9: Complete analysis response**
  - **Validates: Requirements 3.1**

- [x] 2. Migrate Flask backend to hybrid database architecture





  - Install PostgreSQL and MongoDB drivers (psycopg2, pymongo)
  - Update database configuration to support both PostgreSQL and MongoDB connections
  - Implement connection pooling for both databases
  - Create database initialization scripts
  - _Requirements: 5.3, 6.1, 12.1_

- [x] 2.1 Implement PostgreSQL schema


  - Create `users` table with all fields from design (email, password_hash, location, language, etc.)
  - Create `pests` table with multilingual name fields
  - Create `treatments` table with multilingual descriptions
  - Create `ipm_recommendations` table with pest-treatment relationships
  - Create `scans` table with model_version field for traceability
  - Create `feedbacks` table
  - Add all indexes specified in design (email, location, created_at, pest_id, etc.)
  - _Requirements: 6.1, 9.4_

- [x] 2.2 Implement MongoDB collections


  - Create `detection_meta` collection with schema validation
  - Create `feedback` collection
  - Create `analytics` collection for aggregated data
  - Add geospatial index on location field in detection_meta
  - Add text index on pest_label for search
  - _Requirements: 12.1_

- [x] 2.3 Implement ID synchronization between PostgreSQL and MongoDB


  - Modify scan creation to use PostgreSQL serial ID as source of truth
  - Set MongoDB `_id` to format `scan_{postgres_id}` (e.g., "scan_101")
  - Create utility function `sync_detection_metadata()` to link records
  - Implement asynchronous MongoDB write: PostgreSQL insert → get ID → background task writes to MongoDB
  - For MVP: use threading.Thread for background write; for production: use Celery task queue
  - Return API response immediately after PostgreSQL insert (don't wait for MongoDB)
  - _Requirements: 5.3_

- [ ]* 2.4 Write property test for dual database persistence
  - **Property 15: Dual database persistence**
  - **Validates: Requirements 5.3**

- [-] 3. Implement IPM recommendation engine



  - Create `ipm_engine.py` module with recommendation logic
  - Implement rule-based query: `query_ipm_rules(pest_id, crop, region)` that queries `ipm_recommendations` table
  - Implement priority sorting: cultural/biological first, chemical last
  - Implement regional filtering: `filter_by_regulations(recommendations, region)`
  - Return ordered list of recommendations with type, description, priority
  - _Requirements: 4.1, 4.2, 4.4_

- [ ]* 3.1 Write property tests for IPM recommendation logic
  - **Property 11: Recommendation retrieval**
  - **Property 12: IPM priority ordering**
  - **Property 14: Regional treatment filtering**
  - **Validates: Requirements 4.1, 4.2, 4.4**

- [x] 3.2 Implement chemical treatment annotation


  - Add logic to mark all treatments with type="chemical" as "Last Resort"
  - Include safety warnings in chemical treatment descriptions
  - Add visual indicators (warning icons) in response JSON
  - _Requirements: 4.3_

- [ ]* 3.3 Write property test for chemical treatment annotation
  - **Property 13: Chemical treatment annotation**
  - **Validates: Requirements 4.3**

- [x] 3.4 Seed IPM recommendation database



  - Create seed data script with common pests and treatments
  - Add Fall Armyworm, Aphids, Tomato Leafminer, Whitefly, Spider Mites
  - Add cultural controls (crop rotation, intercropping, hand-picking)
  - Add biological controls (parasitic wasps, ladybugs, neem oil, BT spray)
  - Add chemical controls (marked as last resort with warnings)
  - Link pests to treatments with priorities in `ipm_recommendations` table
  - _Requirements: 4.1_

- [x] 4. Integrate AI service with Flask backend





  - Create `ai_client.py` module to communicate with AI microservice
  - Implement `call_ai_service(image_path)` function using requests library
  - Set timeout to 3 seconds for AI service calls (ultimate enforcer of timeout requirement)
  - Handle connection errors, timeouts (requests.exceptions.Timeout), and invalid responses
  - On timeout: return error response "Analysis taking longer than expected. Please try again."
  - Parse AI service JSON response into Python dict
  - _Requirements: 2.2, 2.5_

- [x] 4.1 Update `/analyze` endpoint to use AI microservice


  - Modify existing `/analyze` route to call `ai_client.call_ai_service()`
  - Remove mock `simulate_pest_detection()` function
  - Parse AI response to extract pest_label, confidence, alternatives
  - Look up pest details from PostgreSQL `pests` table
  - Call IPM recommendation engine with pest_id
  - _Requirements: 2.2, 3.1, 4.1_

- [x] 4.2 Implement confidence level classification


  - Create `classify_confidence(score)` function
  - Return "High Confidence" for score >= 0.85
  - Return "Moderate Confidence" for 0.70 <= score < 0.85
  - Return "Low Confidence" for score < 0.70
  - Return "Unable to identify" for score < 0.50
  - _Requirements: 3.2, 3.3, 3.4, 3.5_

- [ ]* 4.3 Write property test for confidence classification
  - **Property 10: Confidence level classification**
  - **Validates: Requirements 3.2, 3.3, 3.4**

- [x] 4.3 Store detection results in hybrid database

  - Insert scan record into PostgreSQL `scans` table
  - Capture returned scan ID (e.g., 101)
  - Insert detailed metadata into MongoDB `detection_meta` with `_id = "scan_101"`
  - Include processing times, model versions, alternatives in MongoDB
  - Store image path in PostgreSQL, full image metadata in MongoDB
  - _Requirements: 5.3, 9.4_

- [x] 4.4 Return complete analysis response to frontend

  - Build JSON response with pest name, scientific name, confidence, confidence_level
  - Include ordered IPM recommendations
  - Include scan_id for feedback submission
  - Add processing time metrics
  - _Requirements: 3.1, 4.2_

- [ ]* 4.5 Write property test for analysis response completeness
  - **Property 9: Complete analysis response**
  - **Validates: Requirements 3.1**

- [x] 5. Checkpoint - Ensure all tests pass





  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Implement feedback collection system





  - Create `POST /api/feedback` endpoint
  - Accept JSON: `{scan_id, is_correct, actual_pest_name, notes}`
  - Validate scan_id exists in PostgreSQL
  - Update PostgreSQL `scans` table: set status="corrected" if is_correct=false
  - Insert feedback record into PostgreSQL `feedbacks` table
  - Insert feedback document into MongoDB `feedback` collection
  - _Requirements: 5.2, 5.3, 5.4_

- [ ]* 6.1 Write property tests for feedback persistence
  - **Property 15: Dual database persistence**
  - **Property 16: Feedback confirmation**
  - **Validates: Requirements 5.3, 5.4**

- [x] 6.2 Implement proactive feedback prompting


  - Modify analysis response to include `should_request_feedback` boolean
  - Set to true when confidence < 0.75
  - Frontend will use this flag to show prominent feedback prompt
  - _Requirements: 5.5_

- [ ]* 6.3 Write property test for proactive feedback request
  - **Property 17: Proactive feedback request**
  - **Validates: Requirements 5.5**

- [x] 6.4 Implement feedback aggregation for model retraining


  - Create background task to aggregate feedback data
  - Count corrections per pest type in MongoDB
  - When count reaches 100 for any pest, log retraining notification
  - Flag corrected images in MongoDB with `flagged_for_retraining: true`
  - _Requirements: 9.1, 9.2_

- [ ]* 6.5 Write property tests for feedback aggregation
  - **Property 31: Feedback aggregation**
  - **Property 32: Retraining threshold trigger**
  - **Validates: Requirements 9.1, 9.2**

- [x] 7. Implement scan history and export







  - Create `GET /api/history` endpoint
  - Query PostgreSQL `scans` table filtered by current_user.id
  - Join with `pests` table to get pest details
  - Order by created_at DESC
  - Return JSON array with date, pest_identified, confidence, severity
  - _Requirements: 6.1, 6.2_

- [ ]* 7.1 Write property tests for history retrieval
  - **Property 18: User scan retrieval**
  - **Property 19: History field completeness**
  - **Validates: Requirements 6.1, 6.2**

- [x] 7.2 Implement historical scan detail view


  - Create `GET /api/history/{scan_id}` endpoint
  - Query PostgreSQL for scan record
  - Query MongoDB for detailed metadata using `_id = "scan_{scan_id}"`
  - Fetch associated recommendations from IPM engine
  - Return complete scan details including image_path
  - _Requirements: 6.3_

- [ ]* 7.3 Write property test for historical detail retrieval
  - **Property 20: Historical detail retrieval**
  - **Validates: Requirements 6.3**

- [x] 7.4 Implement history export functionality


  - Create `GET /api/export/scans?format=json|csv` endpoint
  - Query all scans for current user
  - For JSON: return array of scan objects
  - For CSV: convert to CSV format with headers
  - Set appropriate Content-Type and Content-Disposition headers
  - _Requirements: 6.4_

- [ ]* 7.5 Write property test for export format validity
  - **Property 21: Export format validity**
  - **Validates: Requirements 6.4**

- [x] 8. Implement multi-language support





  - Update context processor to inject language from user profile or Accept-Language header
  - Implement language detection priority: user profile > session > browser header > default 'en'
  - Create `get_localized_pest_name(pest_id, language)` function
  - Query appropriate name field (name_en, name_es, name_hi, name_sw) from `pests` table
  - _Requirements: 7.1, 7.3_

- [ ]* 8.1 Write property tests for localization
  - **Property 22: Browser language detection**
  - **Property 24: Pest name localization**
  - **Validates: Requirements 7.1, 7.3**

- [x] 8.2 Implement language switching


  - Create `POST /api/update_language` endpoint (already exists, verify it works)
  - Update user.language in database
  - Return success response
  - Frontend will reload to apply new language
  - _Requirements: 7.2_

- [ ]* 8.3 Write property test for language switch completeness
  - **Property 23: Language switch completeness**
  - **Validates: Requirements 7.2**

- [x] 8.3 Implement translation fallback


  - Modify translation lookup to check if key exists in selected language
  - If missing, fall back to English translation
  - Log missing translation key to file for future addition
  - _Requirements: 7.5_

- [ ]* 8.4 Write property test for translation fallback
  - **Property 25: Translation fallback**
  - **Validates: Requirements 7.5**

- [x] 9. Implement mobile and offline support

  - Create Service Worker file `sw.js` for offline caching
  - Cache static assets (CSS, JS, images) on install
  - Cache API responses with cache-first strategy for history
  - Implement network-first strategy for analysis endpoint
  - _Requirements: 8.2_

- [ ]* 9.1 Write property test for offline page caching
  - **Property 27: Offline page caching**
  - **Validates: Requirements 8.2**

- [x] 9.2 Implement client-side image compression


  - Add JavaScript function to compress images before upload using Canvas API
  - Target max width/height of 1920px
  - Compress to JPEG quality 85%
  - Reduce file size by ~50-70%
  - _Requirements: 8.4_

- [ ]* 9.3 Write property test for client-side compression
  - **Property 29: Client-side compression**
  - **Validates: Requirements 8.4**

- [x] 9.4 Implement offline image queuing


  - Create IndexedDB store for queued images
  - When offline, save image to IndexedDB with timestamp
  - On connectivity restore (online event), upload queued images
  - Show upload progress in UI
  - _Requirements: 8.3_

- [ ]* 9.5 Write property test for offline image queuing
  - **Property 28: Offline image queuing**
  - **Validates: Requirements 8.3**

- [x] 9.6 Implement request retry mechanism


  - Wrap API calls in retry logic with exponential backoff
  - Show "Retry" button on network errors
  - Cache failed request parameters in sessionStorage
  - Automatically retry on connectivity restore
  - _Requirements: 8.5_

- [ ]* 9.7 Write property test for request retry availability
  - **Property 30: Request retry availability**
  - **Validates: Requirements 8.5**

- [x] 10. Implement responsive mobile UI




  - Add CSS media queries for screen widths < 768px
  - Implement mobile-first layout with flexbox/grid
  - Increase touch target sizes to minimum 44×44px
  - Add viewport meta tag for proper mobile scaling
  - Test on iOS Safari and Android Chrome
  - _Requirements: 8.1_

- [ ]* 10.1 Write property test for responsive interface
  - **Property 26: Responsive interface**
  - **Validates: Requirements 8.1**

- [ ] 11. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 12. Implement security enhancements
  - Migrate password hashing from Werkzeug to Argon2
  - Install argon2-cffi library
  - Update `User.set_password()` to use argon2.PasswordHasher
  - Update `User.check_password()` to use argon2 verification
  - _Requirements: 11.1_

- [ ]* 12.1 Write property test for password hashing
  - **Property 39: Password hashing**
  - **Validates: Requirements 11.1**

- [ ] 12.2 Implement JWT token with 24-hour expiration
  - Verify JWT token generation includes exp claim set to 24 hours from issue time
  - Update login endpoint to set expiration correctly
  - Implement token refresh endpoint (optional)
  - _Requirements: 11.2_

- [ ]* 12.3 Write property test for JWT token issuance
  - **Property 40: JWT token issuance**
  - **Validates: Requirements 11.2**

- [ ] 12.3 Implement HTTPS enforcement
  - Add Flask-Talisman for HTTPS enforcement
  - Configure to require TLS 1.2 or higher
  - Add HSTS headers
  - Redirect HTTP to HTTPS in production
  - _Requirements: 11.3_

- [ ]* 12.4 Write property test for HTTPS enforcement
  - **Property 41: HTTPS enforcement**
  - **Validates: Requirements 11.3**

- [ ] 12.4 Implement image encryption at rest
  - Install cryptography library
  - Create encryption utility using AES-256
  - Encrypt images before saving to disk
  - Decrypt images when serving to users
  - Store encryption keys in environment variables
  - _Requirements: 11.4_

- [ ]* 12.5 Write property test for image encryption
  - **Property 42: Image encryption at rest**
  - **Validates: Requirements 11.4**

- [ ] 12.5 Implement account deletion with GDPR compliance
  - Create `DELETE /api/account` endpoint
  - Mark account for deletion (soft delete initially)
  - Schedule background job to permanently delete data after 30 days
  - Delete from PostgreSQL: user, scans, feedbacks
  - Delete from MongoDB: detection_meta, feedback documents
  - Delete uploaded images from storage
  - Send confirmation email
  - _Requirements: 11.5_

- [ ]* 12.6 Write property test for data deletion compliance
  - **Property 43: Data deletion compliance**
  - **Validates: Requirements 11.5**

- [ ] 13. Implement analytics and outbreak detection
  - Create background task to aggregate detection data
  - Group by region and pest type
  - Calculate occurrence counts per month
  - Store in MongoDB `analytics` collection
  - _Requirements: 12.1_

- [ ]* 13.1 Write property test for location-based aggregation
  - **Property 44: Location-based aggregation**
  - **Validates: Requirements 12.1**

- [ ] 13.2 Implement pest trend query endpoint
  - Create `GET /api/analytics/trends?region=X&pest=Y&period=Z` endpoint
  - Query MongoDB analytics collection
  - Group by pest_type, region, time_period
  - Return aggregated counts
  - _Requirements: 12.2_

- [ ]* 13.3 Write property test for trend query grouping
  - **Property 45: Trend query grouping**
  - **Validates: Requirements 12.2**

- [ ] 13.4 Implement outbreak detection algorithm
  - Calculate historical average occurrences per pest per region
  - Compare current month occurrences to historical average
  - If current > 1.5 × historical, generate outbreak alert
  - Store alert in MongoDB analytics collection
  - _Requirements: 12.3_

- [ ]* 13.5 Write property test for outbreak alert generation
  - **Property 46: Outbreak alert generation**
  - **Validates: Requirements 12.3**

- [ ] 13.6 Implement WebSocket notifications for outbreak alerts
  - Install Flask-SocketIO and Redis for WebSocket support
  - Create WebSocket namespace `/alerts`
  - When outbreak alert generated, emit to all connected clients in affected region
  - Filter recipients by user.location matching alert region
  - _Requirements: 12.4_

- [ ]* 13.7 Write property test for WebSocket alert delivery
  - **Property 47: WebSocket alert delivery**
  - **Validates: Requirements 12.4**

- [ ] 14. Implement model versioning and tracking
  - Add model_version field to AI service configuration
  - Include model_version in AI service response
  - Store model_version in PostgreSQL scans.model_version field
  - Create admin endpoint to view model performance by version
  - _Requirements: 9.4, 9.5_

- [ ]* 14.1 Write property test for model version logging
  - **Property 34: Model version logging**
  - **Validates: Requirements 9.4**

- [ ] 15. Implement performance monitoring
  - Add logging for database query times
  - Log warning when query exceeds 500ms
  - Add logging for AI inference times
  - Create performance metrics endpoint for monitoring
  - _Requirements: 10.4_

- [ ]* 15.1 Write property test for performance warning logging
  - **Property 38: Performance warning logging**
  - **Validates: Requirements 10.4**

- [ ] 16. Create Docker Compose setup for local development
  - Create docker-compose.yml with services: flask-backend, ai-service, postgres, mongodb, redis
  - Configure networking between containers
  - Set up volume mounts for code hot-reloading
  - Add environment variables for database connections
  - Document startup instructions in README

- [ ] 17. Create deployment documentation
  - Document AWS infrastructure setup (ECS, EC2, RDS, MongoDB Atlas)
  - Document environment variables and secrets management
  - Document CI/CD pipeline setup with GitHub Actions
  - Document monitoring and alerting configuration
  - Document backup and disaster recovery procedures

- [ ] 18. Final Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
