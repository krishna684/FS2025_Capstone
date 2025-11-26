# Database Setup Guide

This guide explains how to set up the hybrid PostgreSQL + MongoDB database architecture for the AGBOT AI Pest Detection System.

## Overview

The application uses a hybrid database architecture:
- **PostgreSQL**: Stores structured data (users, pests, treatments, scans, feedback)
- **MongoDB**: Stores semi-structured metadata (detection details, analytics)

## Prerequisites

### PostgreSQL
- PostgreSQL 12 or higher
- Python package: `psycopg2-binary`

### MongoDB
- MongoDB 4.4 or higher
- Python package: `pymongo`

## Quick Start (Development)

For development, the application can run with SQLite instead of PostgreSQL:

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize database
python init_db.py

# Run application
python app.py
```

The development configuration will use:
- SQLite for relational data (falls back automatically)
- Local MongoDB if available (optional for development)

## Production Setup

### 1. Install PostgreSQL

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

**macOS:**
```bash
brew install postgresql
brew services start postgresql
```

**Windows:**
Download and install from [postgresql.org](https://www.postgresql.org/download/windows/)

### 2. Create PostgreSQL Database

```bash
# Connect to PostgreSQL
sudo -u postgres psql

# Create database and user
CREATE DATABASE agbot_db;
CREATE USER agbot_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE agbot_db TO agbot_user;
\q
```

### 3. Install MongoDB

**Ubuntu/Debian:**
```bash
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list
sudo apt update
sudo apt install -y mongodb-org
sudo systemctl start mongod
```

**macOS:**
```bash
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community
```

**Windows:**
Download and install from [mongodb.com](https://www.mongodb.com/try/download/community)

### 4. Create MongoDB Database

```bash
# Connect to MongoDB
mongosh

# Create database and user
use agbot_db
db.createUser({
  user: "agbot_user",
  pwd: "your_secure_password",
  roles: [{ role: "readWrite", db: "agbot_db" }]
})
exit
```

### 5. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here

# PostgreSQL Configuration
POSTGRES_USER=agbot_user
POSTGRES_PASSWORD=your_secure_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=agbot_db

# MongoDB Configuration
MONGO_USER=agbot_user
MONGO_PASSWORD=your_secure_password
MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_DB=agbot_db
```

### 6. Initialize Database

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize database schema and seed data
python init_db.py
```

This will:
- Create all PostgreSQL tables with indexes
- Create MongoDB collections with schema validation
- Create geospatial and text indexes in MongoDB
- Seed initial pest and treatment data
- Create IPM recommendations

### 7. Verify Setup

```bash
# Check PostgreSQL tables
psql -U agbot_user -d agbot_db -c "\dt"

# Check MongoDB collections
mongosh agbot_db --eval "db.getCollectionNames()"
```

## Database Schema

### PostgreSQL Tables

1. **users** - User accounts and profiles
2. **pests** - Pest database with multilingual names
3. **treatments** - Treatment options with multilingual descriptions
4. **ipm_recommendations** - Links pests to treatments with priorities
5. **scans** - Scan history with model version tracking
6. **feedbacks** - User feedback on detections

### MongoDB Collections

1. **detection_meta** - Detailed detection metadata
   - Alternatives, image info, model details, location
   - Geospatial index for location queries
   - Text index for pest label search

2. **feedback** - Detailed feedback with retraining flags
   - Links to detection_meta via scan_id
   - Tracks corrections for model improvement

3. **analytics** - Aggregated pest occurrence data
   - Regional trends and outbreak detection
   - Time-series data for analytics

## Connection Pooling

The application uses connection pooling for both databases:

**PostgreSQL (SQLAlchemy):**
- Pool size: 10 connections
- Max overflow: 20 connections
- Pool recycle: 3600 seconds
- Pre-ping enabled for connection health checks

**MongoDB (PyMongo):**
- Max pool size: 50 connections
- Min pool size: 10 connections
- Max idle time: 45 seconds
- Server selection timeout: 5 seconds

## ID Synchronization

The hybrid architecture uses PostgreSQL as the source of truth for IDs:

1. Insert record into PostgreSQL (e.g., scan)
2. Get auto-generated ID from PostgreSQL
3. Create MongoDB document with ID format: `scan_{postgres_id}`
4. Write to MongoDB asynchronously in background thread
5. Return API response immediately (don't wait for MongoDB)

This ensures:
- Fast response times
- PostgreSQL ACID guarantees
- MongoDB flexibility for metadata
- Consistent IDs across both databases

## Backup and Recovery

### PostgreSQL Backup

```bash
# Backup
pg_dump -U agbot_user agbot_db > backup.sql

# Restore
psql -U agbot_user agbot_db < backup.sql
```

### MongoDB Backup

```bash
# Backup
mongodump --db agbot_db --out /backup/mongodb

# Restore
mongorestore --db agbot_db /backup/mongodb/agbot_db
```

## Troubleshooting

### PostgreSQL Connection Issues

```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Check connection
psql -U agbot_user -d agbot_db -h localhost
```

### MongoDB Connection Issues

```bash
# Check if MongoDB is running
sudo systemctl status mongod

# Check connection
mongosh --host localhost --port 27017
```

### Application Falls Back to SQLite

If PostgreSQL is not available, the application will automatically fall back to SQLite for development. Check logs for connection errors.

### MongoDB Not Available

The application can run without MongoDB - it will log warnings but continue with PostgreSQL only. MongoDB features (detailed metadata, analytics) will be unavailable.

## Migration from SQLite

If you have an existing SQLite database:

```bash
# Run migration script
python migrate_to_hybrid_db.py
```

Note: This creates the new schema. For data migration, consider using a proper migration tool or starting fresh.

## Docker Setup

For containerized deployment, see `docker-compose.yml`:

```bash
# Start all services
docker-compose up -d

# Initialize database
docker-compose exec web python init_db.py
```

## Performance Tuning

### PostgreSQL

Edit `/etc/postgresql/*/main/postgresql.conf`:

```
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 4MB
min_wal_size = 1GB
max_wal_size = 4GB
```

### MongoDB

Edit `/etc/mongod.conf`:

```yaml
storage:
  wiredTiger:
    engineConfig:
      cacheSizeGB: 1
net:
  maxIncomingConnections: 1000
```

## Monitoring

### PostgreSQL

```sql
-- Active connections
SELECT count(*) FROM pg_stat_activity;

-- Slow queries
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
```

### MongoDB

```javascript
// Connection stats
db.serverStatus().connections

// Collection stats
db.detection_meta.stats()
```

## Support

For issues or questions:
1. Check application logs
2. Verify database connections
3. Review this documentation
4. Contact the development team
