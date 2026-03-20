
AGBOT
AI-Driven Agricultural Pest Management Platform
"From Data to Harvest: Smarter Solutions for Farmers"

Final Project Documentation

 
Table of Contents
1. Introduction
  1.1 Project Overview
  1.2 Team Member Introductions
  1.3 Problem Statement
  1.4 Proposed Solution
2. Requirements
  2.1 Hardware Requirements
  2.2 Functional Requirements
  2.3 Non-Functional Requirements
3. System Design
  3.1 System Architecture Overview
  3.2 AI/ML Model Architecture
  3.3 Backend Architecture
  3.4 Frontend Architecture
  3.5 Database Design
  3.6 Cloud Infrastructure
4. Possible Issues
5. Project Related Research
6. Alternate Strategies
7. Development Strategy
8. Development Timeline and Schedule
9. Work Delegation
10. Testing Plan
11. Works Cited
 
1. Introduction
1.1 Project Overview
AGBOT represents an innovative approach to agricultural pest management, leveraging artificial intelligence and machine learning to address one of the most significant challenges facing modern agriculture. The platform enables farmers to identify crop-damaging pests through image analysis and receive actionable, Integrated Pest Management (IPM)-compliant treatment recommendations. Unlike existing agricultural applications that merely detect plant stress symptoms, AGBOT establishes a direct causality link between observed crop damage patterns and the specific insect species responsible, providing farmers with targeted intervention strategies.
The agricultural sector loses approximately 20-40% of global crop production annually due to pest infestations, representing billions of dollars in economic losses. Traditional pest identification methods require expertise that many farmers, particularly those in developing regions, lack access to. AGBOT democratizes this expertise by combining state-of-the-art computer vision models with a comprehensive pest database and intelligent recommendation engine.
1.2 Team Member Introductions
The AGBOT development team comprises four members with complementary expertise spanning machine learning, full-stack development, user experience design, and cloud infrastructure.
Dhanya Boyapally serves as the Computer Vision and Machine Learning Engineer. Dhanya leads the development of the core pest identification models, including dataset curation, model training, and prompt engineering for the Large Language Model (LLM) integration. Responsibilities include ensuring model accuracy exceeds 95% and implementing confidence filtering mechanisms.
Krishna Rithwik Karra functions as the Backend and Frontend Developer. Krishna architects the Node.js/Express API layer, manages database integration with PostgreSQL and MongoDB, and implements the recommendation engine logic. Additional responsibilities include API documentation and end-to-end integration testing.
Jack Frater operates as the Frontend Developer and UI/UX Designer. Jack creates the React-based user interface, develops responsive design systems, and ensures accessibility compliance with WCAG 2.1 AA standards. Responsibilities extend to multilingual support implementation and offline functionality.
Biao Wang serves as the AI Security and DevOps Engineer. Biao manages AWS infrastructure, implements security testing protocols, and oversees model deployment pipelines. Additional responsibilities include adversarial testing, bias auditing, and performance optimization.
The team operates under the mentorship of Professor Noel Aloysius from the College of Agriculture, Food and Natural Resources (CAFNR) at the University of Missouri, who provides domain expertise in agricultural pest management and IPM compliance verification.
1.3 Problem Statement
Current agricultural pest management applications suffer from a critical limitation: the inability to connect observed crop damage to specific pest species. Existing solutions, such as Plantix, PlantSnap, and Agrio, can detect that a plant exhibits signs of stress, disease, or damage, but cannot identify which insect caused the damage. This gap forces farmers to either consult expensive agricultural extension services, apply broad-spectrum pesticides indiscriminately, or simply guess at the cause.
The consequences of this knowledge gap are significant. Misidentification leads to inappropriate treatment selection, resulting in continued crop losses despite intervention. Overuse of chemical pesticides contributes to environmental degradation, pesticide resistance development, and increased production costs. Furthermore, beneficial insects that serve as natural pest predators are often eliminated alongside target pests, disrupting ecological balance and creating conditions for future outbreaks.
The target user population includes smallholder farmers in developing regions who lack access to agricultural extension services, commercial farmers seeking to optimize pest management efficiency, agricultural cooperatives managing large-scale operations, and research institutions studying pest distribution patterns. These users require a solution that operates effectively with limited connectivity, supports multiple languages, and provides recommendations aligned with regional regulatory frameworks.
1.4 Proposed Solution
AGBOT addresses these challenges through a Damage-to-Insect Causality Engine that analyzes uploaded images of crop damage and identifies the responsible pest species with high confidence. The system then generates IPM-compliant treatment recommendations prioritizing non-chemical interventions where feasible.
The solution architecture consists of four integrated components. The Image Analysis Pipeline processes farmer-submitted photographs through preprocessing, feature extraction, and classification stages. The Pest Identification Engine employs ensemble deep learning models to match damage patterns against a comprehensive database of pest signatures. The Recommendation Engine applies rule-based logic combined with machine learning-based ranking to generate treatment options. Finally, the User Interface provides an accessible, multilingual platform supporting offline functionality for rural deployment.
Key differentiating features include sub-3-second processing time from image upload to recommendation delivery, support for 20+ initial languages with infrastructure for 100+ future languages, offline-first architecture for areas with limited connectivity, and feedback mechanisms enabling continuous model improvement through farmer-verified outcomes.
 
2. Requirements
2.1 Hardware Requirements
AGBOT deployment requires hardware infrastructure across three tiers: client devices, server infrastructure, and storage systems.
2.1.1 Client Device Requirements
End users access AGBOT through smartphones or tablets capable of capturing high-resolution images. Minimum specifications include a camera resolution of 8 megapixels or higher, 2GB RAM, and Android 8.0+ or iOS 12+ operating system support. The application targets a download size under 50MB to accommodate users with limited storage and bandwidth.
2.1.2 Server Infrastructure
The backend infrastructure requires GPU-accelerated compute instances for AI inference operations. AWS g4dn.xlarge instances provide the necessary NVIDIA T4 GPU capabilities for production workloads. The deployment architecture utilizes multiple availability zones to ensure 99.9% uptime, with auto-scaling groups configured to handle traffic spikes during agricultural seasons.
2.1.3 Storage Requirements
Data storage requirements span relational and document databases. PostgreSQL RDS instances store transactional data including user accounts, pest identification records, and IPM recommendation databases. MongoDB Atlas clusters store unstructured data including image metadata, analytics events, and feedback submissions. Total storage provisioning accounts for 500GB initial capacity with auto-scaling enabled.
2.2 Functional Requirements
Functional requirements define the specific capabilities AGBOT must deliver to users.
ID	Requirement	Description
FR-01	User Authentication	Secure registration and login with JWT tokens; optional OAuth 2.0 social login support
FR-02	Image Upload	Camera capture and gallery upload with automatic preprocessing and compression
FR-03	Pest Identification	AI-powered analysis returning pest species with confidence scores and visual indicators
FR-04	Treatment Recommendations	IPM-compliant recommendations ranked by efficacy, cost, and environmental impact
FR-05	Feedback Collection	User verification of identification accuracy and treatment effectiveness for model retraining
FR-06	History Tracking	Complete record of past identifications with filtering and search capabilities
FR-07	Multilingual Support	Interface localization for 20+ languages with RTL support for Arabic, Hebrew, and Urdu
Table 1: Functional Requirements Summary
2.3 Non-Functional Requirements
Non-functional requirements establish quality attributes governing system performance, security, and usability.
2.3.1 Performance Requirements
The system must achieve end-to-end processing time under 3 seconds from image submission to recommendation display. This budget allocates approximately 50ms for image preprocessing, 1.5 seconds for model inference, 500ms for recommendation generation, and 950ms for network overhead and rendering. The infrastructure must support 10,000 concurrent users during peak agricultural seasons without performance degradation.
2.3.2 Reliability Requirements
AGBOT targets 99.9% uptime availability, translating to maximum allowable downtime of 8.76 hours annually. This requirement necessitates multi-region deployment, automated failover mechanisms, and comprehensive monitoring with alerting thresholds. Database backup procedures must support point-in-time recovery with maximum 1-hour data loss window.
2.3.3 Security Requirements
All data transmission must utilize HTTPS encryption with TLS 1.3. User passwords require Argon2 hashing with parameters optimized for security (memory: 65,536KB, iterations: 3, parallelism: 4). The system must comply with GDPR and CCPA data protection regulations, implementing user data export and deletion capabilities. Rate limiting prevents brute force attacks with 5-failure lockout triggering 15-minute account suspension.
2.3.4 Accessibility Requirements
The user interface must achieve WCAG 2.1 AA compliance, ensuring accessibility for users with visual, auditory, motor, or cognitive disabilities. Specific requirements include keyboard navigation support, screen reader compatibility, minimum contrast ratios of 4.5:1 for normal text, and support for text scaling up to 200% without horizontal scrolling.
 
3. System Design
3.1 System Architecture Overview
AGBOT employs a microservices architecture separating concerns across API gateway, AI inference, recommendation engine, and data persistence layers. This design enables independent scaling of compute-intensive AI workloads while maintaining low-latency API responses for user interactions.
The architecture follows a three-tier model and Monolithic MVC. The presentation tier consists of React-based web and mobile applications communicating via REST APIs and WebSocket connections for real-time updates. The application tier comprises Node.js/Express API gateway handling authentication, request routing, and response aggregation, alongside Python/FastAPI microservices dedicated to AI inference operations. The data tier utilizes PostgreSQL for transactional data and MongoDB for document storage, with Redis caching reducing database load for frequently accessed resources.
3.2 AI/ML Model Architecture
The pest identification system employs an ensemble approach combining EfficientNet-B0 as the primary classifier with ResNet-50 as a fallback model for low-confidence predictions.
3.2.1 Primary Model: EfficientNet-B0
EfficientNet-B0 was selected based on its optimal balance of accuracy and computational efficiency. Research demonstrates that EfficientNet-B0 achieves 99.71% accuracy on plant disease classification tasks while requiring only 13.3MB model size and 1-2 second inference time on GPU instances. The architecture utilizes compound scaling to uniformly scale network width, depth, and resolution, achieving superior performance compared to larger models through efficient parameter utilization.
Model optimization includes INT8 quantization reducing inference latency by 30-40% while maintaining accuracy within 1% of the full-precision baseline. The quantized model enables deployment on edge devices for offline inference scenarios.
3.2.2 Fallback Model: ResNet-50
ResNet-50 serves as the fallback classifier activated when EfficientNet-B0 confidence scores fall below the 85% threshold. Despite its larger 98MB model size, ResNet-50 provides robust feature extraction through residual connections that mitigate gradient degradation in deep networks. The ensemble approach improves overall system accuracy by 5-10% compared to single-model deployment.
3.2.3 Inference Pipeline
The inference pipeline processes images through the following stages: image reception and validation, preprocessing (resize to 224×224, histogram equalization, normalization), primary model inference with EfficientNet-B0, confidence evaluation against threshold, conditional fallback to ResNet-50, result aggregation, and response formatting. Total pipeline latency remains under 2 seconds for 95th percentile requests.
3.3 Backend Architecture
The backend employs a hybrid architecture combining Node.js/Express for API gateway functions with Python/FastAPI for AI inference microservices.
3.3.1 API Gateway (Node.js/Express)
Node.js/Express handles user-facing API endpoints including authentication, image upload, history retrieval, and feedback submission. Benchmarks demonstrate Express achieving 55,200 requests per second under load testing conditions, providing substantial headroom for the 10,000 concurrent user requirement. The event-driven architecture efficiently manages I/O-bound operations without blocking threads.
Key API endpoints include /api/auth (registration, login, token refresh), /api/detect (image upload and pest identification), /api/history (past identification retrieval), /api/feedback (user verification submission), and /api/recommendations (treatment option retrieval).
3.3.2 AI Inference Service (Python/FastAPI)
Python/FastAPI microservices handle AI inference operations, leveraging Python's extensive machine learning ecosystem. FastAPI achieves 35,000-40,000 requests per second while providing native async/await support and automatic OpenAPI documentation generation. Communication between Express gateway and FastAPI services utilizes gRPC for low-latency internal calls.
3.4 Frontend Architecture
The frontend utilizes React with TypeScript and Monolithic Flask, selected for its extensive ecosystem, component reusability, and React Native pathway for mobile development.
3.4.1 Technology Stack
The frontend stack will comprises: Vite for build tooling with hot module replacement, react-query for server state management and caching, Zustand for client state management, react-i18next for internationalization, Socket.io for real-time WebSocket connections, Leaflet for geospatial mapping features, and Workbox for service worker generation enabling offline functionality or traditional server-rendered approach without a JavaScript build pipeline
3.4.2 Component Architecture
The application follows atomic design principles organizing components into atoms (buttons, inputs), molecules (form fields, cards), organisms (navigation, result displays), templates (page layouts), and pages (complete views). This hierarchy promotes reusability while maintaining consistent styling through a centralized design system.
3.4.3 Offline Support
Service workers cache critical assets and recent API responses enabling core functionality without network connectivity. Users can capture and queue images for later submission when connectivity resumes. Previously retrieved identification results and recommendations remain accessible offline through IndexedDB storage.
3.5 Database Design
AGBOT employs a polyglot persistence strategy utilizing PostgreSQL for transactional data and MongoDB for document storage[12].
3.5.1 PostgreSQL Schema
PostgreSQL stores structured, relational data requiring ACID compliance. Primary tables include: users (authentication credentials, profile information), identifications (pest detection records linked to users), recommendations (IPM treatment options with regulatory metadata), and feedback (user-submitted verification data). PostGIS extension enables geospatial queries for regional pest distribution analysis.
3.5.2 MongoDB Collections
MongoDB stores unstructured and semi-structured data benefiting from flexible schema design. Collections include: image_metadata (uploaded image properties, preprocessing parameters), analytics_events (user interaction tracking), and pest_knowledge (evolving pest characteristic data). GeoJSON support enables geospatial indexing for location-based queries.
3.6 Cloud Infrastructure
AGBOT deploys on Amazon Web Services utilizing multi-region architecture for high availability and low latency[13].
3.6.1 Compute Resources
Primary deployment resides in us-east-1 utilizing g4dn.xlarge instances with NVIDIA T4 GPUs for AI inference. Secondary regions (eu-west-1, ap-south-1) provide geographic distribution reducing latency for international users. Auto-scaling groups adjust capacity based on CPU utilization and request queue depth, with reserved instances covering baseline load and spot instances handling burst traffic.
3.6.2 Content Delivery
Amazon CloudFront CDN distributes static assets globally with edge caching reducing origin load by 70-80%. Dynamic API responses utilize Lambda@Edge for request routing and response optimization. Estimated monthly infrastructure costs range from $8,000-$12,000 for 10,000 concurrent farmer support.
 
4. Possible Issues
Several technical challenges present ongoing risks to AGBOT development and deployment. These issues lack guaranteed solutions and require continuous monitoring and iterative mitigation strategies.
4.1 Dataset Scarcity for Rare Pests
Some agricultural pests, particularly newly invasive species or those endemic to specific regions, lack sufficient publicly available image datasets for effective model training. This limitation reduces model generalization capability and may result in low-confidence or incorrect identifications for uncommon pest species. Mitigation strategies include synthetic data augmentation, partnerships with agricultural research institutions, and implementing "Unknown/Uncertain" output categories with guidance for manual expert consultation.
4.2 LLM Hallucination in Edge Cases
Despite prompt engineering safeguards, large language models can generate misleading explanations when encountering unseen scenarios such as pest-crop combinations not represented in training data or unusual climatic conditions. These hallucinations pose regulatory and safety risks if farmers act on incorrect recommendations. Mitigation includes strict output templates, human review requirements for borderline cases, continuous output monitoring, and feedback loops to refine prompt constraints.
4.3 Cross-Regional Pest Variability
The same pest species may exhibit morphological differences across geographic regions due to climate variations, seasonal timing, and local crop varieties. These differences can reduce model confidence when processing images from underrepresented regions. Solutions under investigation include region-specific model fine-tuning, user-specified location parameters for calibration, and collaboration with regional agricultural extension offices to expand training data diversity.
4.4 Computational Cost of Retraining
As the system accumulates user feedback and new pest images, periodic model retraining becomes necessary to maintain accuracy. Large-scale retraining requires significant GPU resources and incurs substantial cloud computing costs. The team is exploring incremental learning approaches, transfer learning techniques to minimize full retraining requirements, and scheduled retraining during off-peak hours to optimize infrastructure utilization.
4.5 Prompt Injection Attacks
Malicious users might craft image metadata or text inputs designed to manipulate LLM behavior, potentially causing the system to ignore safety rules or generate inappropriate recommendations. Security measures include input sanitization, strict prompt template enforcement, rate limiting, and continuous monitoring of suspicious output patterns.
4.6 Mobile Responsiveness Under Poor Connectivity
Farmers in remote agricultural regions frequently operate on 2G/3G networks with intermittent connectivity. Ensuring responsive application behavior and successful image uploads under these conditions requires careful optimization. Implementation strategies include progressive image compression before upload, service worker caching for offline functionality, lazy loading of non-essential resources, and local caching of historical recommendations.
 
5. Project Related Research
Extensive research informed technology selection decisions across all system components. This section summarizes key findings from the research phase.
5.1 AI Model Selection Research
The model selection process evaluated four architecture families against AGBOT's requirements for ≥95% accuracy with sub-3-second inference on resource-constrained deployments[14].
ResNet-50 demonstrated 95%+ accuracy with established training methodologies but requires 98MB storage. EfficientNet-B0 achieved 99.71% accuracy on benchmark datasets while requiring only 13.3MB storage and 1-2 second inference time, representing the optimal accuracy-efficiency tradeoff. Vision Transformers (ViT) achieved highest accuracy at 99.8% but require large datasets exceeding 14 million images and exhibit slower inference on edge devices. Hybrid CNN+ViT architectures show 15-25% improvement over single-architecture baselines but introduce deployment complexity.
Based on this analysis, EfficientNet-B0 was selected as the primary model with ResNet-50 serving as the fallback for low-confidence scenarios.
5.2 Backend Framework Research
Backend framework evaluation prioritized support for 10,000+ concurrent users, sub-3-second response times, and seamless AI integration[15].
Node.js/Express demonstrated 55,200 requests per second throughput with event-driven architecture efficiently handling I/O operations. Python/FastAPI achieved 35,000-40,000 requests per second while providing excellent Python ML library integration for AI workloads. Java/Spring Boot offers enterprise stability but exhibits higher memory footprint and verbose configuration requirements.
The hybrid architecture combining Express for API gateway with FastAPI for AI inference leverages the strengths of both frameworks.
5.3 Database Selection Research
Database evaluation balanced requirements for strong consistency in transactional data, flexible schema for evolving pest metadata, and sub-500ms query performance[16].
PostgreSQL provides ACID compliance essential for user data integrity, PostGIS extensions for geospatial analysis, and mature tooling for complex analytical queries. MongoDB offers flexible document schema accommodating evolving pest characteristic data, horizontal scaling for high-volume writes, and native JSON storage aligning with API response formats.
The polyglot persistence strategy assigns PostgreSQL for users, identifications, and regulatory data while MongoDB handles image metadata and analytics events.
5.4 Dataset Acquisition Research
Training data strategy addresses the challenge of acquiring sufficient diverse images for robust model generalization[17].
PlantVillage dataset provides 54,000 images under controlled laboratory conditions achieving 99% accuracy but degrading to 60-70% on real-world field images. IP102 dataset contains 75,000 images captured in actual agricultural settings across 102 pest species, demonstrating 64.40% baseline accuracy more representative of production performance. Custom labeling through Labelbox enables targeted data collection for underrepresented categories at $0.15-$1.00 per image.
The multi-phase strategy combines PlantVillage and IP102 for initial training (Phase 1), Labelbox custom labeling for gap filling (Phase 2), and farmer feedback integration for continuous improvement (Phase 3).
5.5 IPM Recommendation Engine Research
Recommendation engine design balances regulatory compliance, practical effectiveness, and user trust[18].
Rule-based expert systems provide explainable, auditable recommendations aligned with regulatory requirements but cannot adapt to emerging patterns. AI-driven recommendation systems learn from outcome data but produce black-box decisions difficult to validate. USDA National IPM Database offers authoritative guidance for 500+ crops but limited to United States coverage.
The hybrid architecture implements rule-based foundations maintained by agricultural experts, AI-powered ranking trained on farmer outcome data, and regulatory database integration for compliance filtering.
5.6 Authentication and Security Research
Security architecture evaluation prioritized frictionless user experience while maintaining robust protection against attacks[19].
JWT authentication enables stateless, scalable session management suitable for mobile deployments but tokens remain valid until expiration. OAuth 2.0 provides industry-standard social login integration with instant logout capability but introduces implementation complexity. Argon2 hashing demonstrates superior password protection compared to bcrypt with configurable memory-hard parameters.
The selected approach combines JWT for primary authentication (24-hour expiration), optional OAuth 2.0 for social login convenience, and Argon2 hashing (memory: 65,536KB, iterations: 3, parallelism: 4) achieving approximately 50ms verification time.
 
6. Alternate Strategies
For each major architectural decision, alternative approaches were evaluated and documented for potential future consideration.
6.1 AI Model Alternatives
Should EfficientNet-B0 fail to meet accuracy requirements in production, three fallback strategies exist. First, ensemble deployment running both EfficientNet and ResNet on every prediction improves accuracy by 5-10% at the cost of increased latency. Second, Vision Transformer adoption becomes viable if training data exceeds 1 million images through farmer feedback accumulation. Third, custom architecture development through neural architecture search could optimize specifically for pest identification domain characteristics.
6.2 Backend Architecture Alternatives
If the Node.js/FastAPI hybrid introduces excessive operational complexity, consolidation options include full Python deployment using Django or Flask with Celery for async tasks, or full Node.js deployment leveraging TensorFlow.js for JavaScript-native inference. Additionally, serverless architecture using AWS Lambda could reduce operational overhead for variable traffic patterns at the cost of cold start latency.
6.3 Database Alternatives
If polyglot persistence proves difficult to maintain, single-database consolidation options exist. PostgreSQL with JSONB columns can accommodate semi-structured data currently stored in MongoDB. Alternatively, CockroachDB offers PostgreSQL compatibility with native horizontal scaling, potentially simplifying the architecture while maintaining relational semantics.
6.4 Cloud Provider Alternatives
While AWS was selected for its comprehensive AI/ML tooling, alternative providers offer competitive advantages. Google Cloud Platform provides Vertex AI with integrated model training and TPU access at competitive pricing ($463/month for equivalent workloads). Microsoft Azure offers lowest GPU instance pricing ($447/month) with strong enterprise integration. Multi-cloud deployment remains an option if vendor lock-in concerns materialize.
6.5 Model Deployment Alternatives
ONNX Runtime with TensorRT optimization was selected for model serving, but alternatives exist if compatibility issues arise. TorchServe provides native PyTorch model support with efficient batching and built-in model versioning. TensorFlow Serving offers mature production deployment for TensorFlow models. Triton Inference Server supports multiple framework formats with advanced batching and ensemble capabilities.
 
7. Development Strategy
AGBOT development follows an Agile-Spiral Hybrid methodology combining iterative sprints with risk-driven validation loops[20].
7.1 Rationale for Agile-Spiral Hybrid
Pure Waterfall methodology is unsuitable for AGBOT because AI systems exhibit non-deterministic behavior dependent on data quality and hyperparameter tuning rather than fixed specifications. Risk-driven validation is essential as security, bias, and accuracy issues emerge through testing rather than upfront design. Early farmer feedback enables rapid iteration on recommendation quality and IPM compliance. Cross-component integration between frontend, backend, AI, and database layers requires iterative coordination.
The Agile-Spiral Hybrid combines Agile methodology for iterative sprints, continuous stakeholder feedback, and adaptive planning with Spiral model principles for risk-driven loops, early prototype validation, and incremental risk mitigation.
7.2 Sprint Structure
Development proceeds through four-week Spiral Loops, each containing five stages:
1.	Planning and Risk Assessment (3-4 days): Define sprint goals, identify technical risks, prioritize features, and align with team capacity.
2.	Development and Prototyping (8-10 days): Implement features across frontend, backend, and AI subsystems with parallel development streams.
3.	Testing and Validation (4-5 days): Execute unit tests, integration tests, model validation, and security testing.
4.	Risk Analysis and Feedback Collection (2-3 days): Conduct stakeholder reviews, collect user feedback, perform bias analysis, and profile performance.
5.	Deployment and Iteration (1-2 days): Deploy incremental builds, collect metrics, and refine backlog for subsequent sprints.
7.3 Stakeholder Engagement
Regular communication ensures alignment between development progress and stakeholder expectations. Bi-weekly mentor check-ins with Professor Aloysius review progress, validate IPM compliance, and provide agricultural domain guidance. Monthly farmer feedback sessions gather input on usability, recommendation accuracy, and practical applicability when field testing is feasible. Weekly team standups (15 minutes) synchronize on blockers, dependencies, and resource allocation.
7.4 Adaptation Triggers
Development direction shifts based on defined trigger conditions:
•	Model accuracy below 90%: Activate data augmentation sprint and extend training phase
•	API latency exceeding 2 seconds: Optimize database queries, add caching, revisit architecture
•	Critical security vulnerability discovered: Pause feature development for emergency security sprint
•	Stakeholder requirement change: Reassess timeline with potential 1-2 week extension
•	Key team member unavailability: Redistribute tasks using RACI matrix and activate contingency plan
 
8. Development Timeline and Schedule
AGBOT development spans 16 weeks across four Spiral Loops, organized into six parallel workstreams: AI/ML, Backend, Frontend, Database, Infrastructure, and Integration.
8.1 Sprint 1: Foundation (Weeks 1-4)
Sprint 1 establishes foundational infrastructure and baseline AI capabilities.
•	AI/ML: Dataset preparation, EfficientNet-B0 baseline training, initial validation
•	Backend: Node.js API scaffold, JWT authentication implementation
•	Frontend: React project setup, component library initialization
•	Database: PostgreSQL schema design, MongoDB collection design
•	Infrastructure: AWS account setup, Docker containerization
Milestone: Baseline AI model trained with >90% validation accuracy; API skeleton operational.
8.2 Sprint 2: Integration (Weeks 5-8)
Sprint 2 focuses on component integration and end-to-end functionality.
•	AI/ML: ResNet-50 fallback model training, confidence filtering implementation, LLM integration
•	Backend: /api/detect, /api/history, /api/feedback endpoint development
•	Frontend: Image upload interface, result display screens, feedback form components
•	Database: PostgreSQL and MongoDB deployment, index creation
•	Integration: AI service connection to backend API
Milestone: End-to-end pest detection working; AI and API fully integrated.
8.3 Sprint 3: Enhancement (Weeks 9-12)
Sprint 3 delivers advanced features and production hardening.
•	AI/ML: Prompt engineering refinement, IPM rule validation, bias testing
•	Backend: Recommendation engine implementation, enhanced error handling
•	Frontend: History view, settings interface, multilingual UI, offline support
•	Infrastructure: Auto-scaling configuration, CDN setup, monitoring implementation
Milestone: Full AI pipeline functional; recommendations generated with IPM compliance.
8.4 Sprint 4: Finalization (Weeks 13-16)
Sprint 4 completes development with final validation and deployment preparation.
•	AI/ML: Model retraining with feedback data, final accuracy validation
•	Backend: Rate limiting, comprehensive logging, security hardening
•	Frontend: WCAG 2.1 AA accessibility compliance, responsive design polish
•	Deployment: Staging environment testing, documentation finalization
Milestone: System deployment-ready; all requirements validated; beta testing prepared.
8.5 Critical Path Dependencies
The following dependencies define the critical path requiring careful monitoring:
•	Week 4: Dataset labeled and baseline model trained → enables backend development
•	Week 6: API endpoints functional → enables frontend integration
•	Week 8: AI service integrated with backend → enables recommendation engine
•	Week 10: Full pipeline working → enables security and bias testing
•	Week 14: All features complete → enables final testing phase
•	Week 16: System deployment-ready → production or beta release
Buffer time of 1-2 weeks is incorporated into the schedule for model retraining, bug fixes, or unforeseen delays.
 
9. Work Delegation
9.1 Team Role Assignments
Work delegation follows role-based assignment aligned with team member expertise.
Team Member	Primary Role	Key Responsibilities
Dhanya Boyapally	AI/ML Engineer	CNN model training, dataset management, prompt engineering, feature extraction, model optimization
Krishna Rithwik Karra	Backend Developer	Node.js API development, database integration, recommendation engine logic, API documentation, integration testing
Jack Frater	Frontend/UI/UX	React components, UI mockups, responsive design, accessibility compliance, multilingual support, user testing coordination
Biao Wang	DevOps/Security	AWS infrastructure, security testing, model deployment, performance optimization, monitoring configuration
Table 2: Team Role Assignments
9.2 RACI Matrix
The RACI (Responsible, Accountable, Consulted, Informed) matrix clarifies decision-making authority for key deliverables.
Task	Dhanya	Krishna	Jack	Biao
Dataset Collection	R/A	I	I	C
Model Training	R/A	I	I	C
API Development	C	R/A	I	C
Frontend Development	I	C	R/A	I
Security Testing	C	I	I	R/A
Infrastructure Setup	I	C	I	R/A
Integration Testing	C	R/A	C	C
Documentation	C	R	R	A
Table 3: RACI Matrix (R=Responsible, A=Accountable, C=Consulted, I=Informed)
9.3 Task Handoff Points
Critical handoff dependencies ensure smooth workflow transitions:
•	Weeks 2-4: Dhanya delivers labeled dataset → Krishna begins database schema implementation
•	Week 4: Dhanya delivers baseline model → Biao begins Docker containerization
•	Week 6: Krishna delivers API scaffold → Jack integrates image upload component
•	Week 7: Dhanya delivers trained models → Krishna integrates into /api/detect
•	Week 8: Krishna delivers integrated API → Jack connects frontend to backend
•	Week 10: Biao delivers security testing results → Team addresses vulnerabilities
•	Week 12: Dhanya delivers retrained models → Biao re-deploys to staging
•	Week 16: Entire team validates deployment checklist → System ready for production
 
10. Testing Plan
The AGBOT testing strategy employs a multi-layered approach covering unit testing, integration testing, end-to-end testing, AI model validation, security testing, and performance testing[21].
10.1 Unit Testing
Jest serves as the primary unit testing framework, executing daily with target runtime under 2 minutes and minimum 80% code coverage. Unit tests verify individual function behavior in isolation, covering API endpoint handlers, database query functions, frontend component rendering, and utility functions. Test execution occurs automatically on every commit through GitHub Actions integration.
10.2 Integration Testing
Integration tests validate interaction between system components, executing nightly on the staging environment. Key integration test scenarios include frontend-to-API communication verification, API-to-database CRUD operation validation, API-to-AI service inference pipeline testing, and authentication flow end-to-end verification.
10.3 End-to-End Testing
Cypress provides end-to-end testing capabilities, executing weekly with target runtime under 10 minutes. E2E tests simulate complete user workflows including user registration and login, image upload and pest identification, recommendation viewing and feedback submission, and history browsing and filtering. Testing focuses on critical user paths rather than exhaustive coverage to maintain reasonable execution time.
10.4 AI Model Validation
AI model validation occurs monthly following each retraining cycle. Validation utilizes a 5,000-image holdout test set never exposed during training. Key metrics include overall accuracy (target: ≥95%), per-class precision and recall, confidence score calibration, and latency distribution (target: p95 < 2 seconds). Model deployment proceeds only if accuracy degradation remains under 1% compared to the previous version.
10.5 Security Testing
Security testing combines automated scanning with manual penetration testing. SonarQube executes continuous static analysis on every commit, identifying code vulnerabilities and security hotspots. Monthly security audits include adversarial image testing (10+ malicious/edge-case images), prompt injection attack simulation, authentication bypass attempts, and API rate limiting verification.
10.6 Performance Testing
k6 provides load testing capabilities, executing monthly with scenarios ramping to 10,000 concurrent users. Performance test scenarios verify API response times under load (target: p95 < 3 seconds), database query performance under concurrent access, CDN effectiveness for static asset delivery, and auto-scaling group response to traffic spikes.
10.7 CI/CD Pipeline Integration
All testing integrates into the GitHub Actions CI/CD pipeline with the following stages:
1.	Build and Lint (2 minutes): Code compilation, ESLint static analysis
2.	Unit Tests (2 minutes): Jest test suite execution with coverage reporting
3.	Security Scan (1 minute): SonarQube vulnerability analysis
4.	Staging Deployment (5 minutes): Automated deployment to staging environment
5.	Integration Tests (5 minutes): Cross-component validation
6.	Canary Deployment (1 hour): 5% production traffic routing with monitoring
7.	Production Promotion: Full deployment if canary metrics meet thresholds
 
11. Works Cited
[1] United States Department of Agriculture. "Integrated Pest Management (IPM) Principles." USDA National Institute of Food and Agriculture, 2023. https://www.usda.gov/topics/farming/ipm.
[2] Food and Agriculture Organization of the United Nations. "The State of Food and Agriculture 2021: Making Agrifood Systems More Resilient to Shocks and Stresses." FAO, 2021. https://www.fao.org/publications.
[3] Mohanty, Sharada P., David P. Hughes, and Marcel Salathé. "Using Deep Learning for Image-Based Plant Disease Detection." Frontiers in Plant Science, vol. 7, 2016, Article 1419. https://doi.org/10.3389/fpls.2016.01419.
[4] Amazon Web Services. "Amazon EC2 G4 Instances." AWS Documentation, 2024. https://aws.amazon.com/ec2/instance-types/g4/.
[5] Nielsen, Jakob. "Response Times: The 3 Important Limits." Nielsen Norman Group, 1993. https://www.nngroup.com/articles/response-times-3-important-limits/.
[6] Biryukov, Alex, Daniel Dinu, and Dmitry Khovratovich. "Argon2: The Memory-Hard Function for Password Hashing and Other Applications." University of Luxembourg, 2015. https://www.password-hashing.net/argon2-specs.pdf.
[7] Tan, Mingxing, and Quoc V. Le. "EfficientNet: Rethinking Model Scaling for Convolutional Neural Networks." Proceedings of the 36th International Conference on Machine Learning, PMLR, 2019, pp. 6105-6114.
[8] Atila, Ümit, et al. "Plant Leaf Disease Classification Using EfficientNet Deep Learning Model." Ecological Informatics, vol. 61, 2021, Article 101182. https://doi.org/10.1016/j.ecoinf.2020.101182.
[9] He, Kaiming, et al. "Deep Residual Learning for Image Recognition." Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition, 2016, pp. 770-778.
[10] Tiangolo, Sebastián Ramírez. "FastAPI Documentation." FastAPI, 2024. https://fastapi.tiangolo.com/.
[11] Meta Platforms, Inc. "React: A JavaScript Library for Building User Interfaces." React Documentation, 2024. https://react.dev/.
[12] Sadalage, Pramod J., and Martin Fowler. NoSQL Distilled: A Brief Guide to the Emerging World of Polyglot Persistence. Addison-Wesley Professional, 2012.
[13] Amazon Web Services. "AWS Well-Architected Framework." AWS Documentation, 2024. https://aws.amazon.com/architecture/well-architected/.
[14] Dosovitskiy, Alexey, et al. "An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale." International Conference on Learning Representations, 2021.
[15] Node.js Foundation. "Node.js Documentation." Node.js, 2024. https://nodejs.org/en/docs/.
[16] PostgreSQL Global Development Group. "PostgreSQL Documentation." PostgreSQL, 2024. https://www.postgresql.org/docs/.
[17] Wu, Xiaoping, et al. "IP102: A Large-Scale Benchmark Dataset for Insect Pest Recognition." Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition, 2019, pp. 8787-8796.
[18] Damos, Petros. "Modular Structure of Web-Based Decision Support Systems for Integrated Pest Management." Agronomy, vol. 5, no. 3, 2015, pp. 423-438.
[19] Auth0. "JSON Web Token (JWT) Introduction." JWT.io, 2024. https://jwt.io/introduction.
[20] Boehm, Barry W. "A Spiral Model of Software Development and Enhancement." Computer, vol. 21, no. 5, 1988, pp. 61-72.
[21] Fowler, Martin. "Continuous Integration." MartinFowler.com, 2006. https://martinfowler.com/articles/continuousIntegration.html.
