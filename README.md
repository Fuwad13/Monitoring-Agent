# Monitoring Agent

A powerful monitoring system that tracks changes in LinkedIn profiles, company pages, and websites, providing real-time notifications and AI-powered insights about detected changes.

## 🚀 Overview

The Monitoring Agent is a comprehensive web scraping and monitoring solution built with FastAPI, Celery, and modern Python technologies. It enables users to:

- **Monitor LinkedIn Profiles & Companies**: Track changes in professional profiles and company pages
- **Website Monitoring**: Monitor any website for content changes
- **AI-Powered Analysis**: Uses Google Gemini AI to analyze and summarize detected changes
- **Real-time Notifications**: Email alerts when changes are detected
- **RESTful API**: Complete API for managing monitoring targets and viewing results
- **Background Processing**: Asynchronous task processing with Celery and Redis
- **Scheduled Monitoring**: Configurable check frequencies for each target

## ✨ Features

- 🔍 **Multi-Platform Monitoring**: LinkedIn profiles, company pages, and general websites
- 🤖 **AI Integration**: Google Gemini for intelligent change analysis
- 📧 **Email Notifications**: Automated alerts with change summaries
- 🔐 **User Authentication**: JWT-based secure user management
- 📊 **Change History**: Complete audit trail of all detected changes
- ⏰ **Flexible Scheduling**: Customizable monitoring frequencies
- 🔄 **Background Tasks**: Non-blocking monitoring with Celery
- 📱 **RESTful API**: Full CRUD operations for all resources
- 🎯 **Snapshot System**: Historical data preservation for LinkedIn targets

## 🏗️ Architecture Overview

### System Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │    │  Celery Worker  │    │  Celery Beat    │
│   (REST API)    │    │ (Task Executor) │    │  (Scheduler)    │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │       Redis Queue       │
                    │   (Task Distribution)   │
                    └─────────────────────────┘
                                 │
          ┌──────────────────────┼──────────────────────┐
          │                      │                      │
          ▼                      ▼                      ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    MongoDB      │    │  Google Gemini  │    │   Email SMTP    │
│   (Database)    │    │   (AI Analysis) │    │ (Notifications) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Data Flow

1. **User Registration & Authentication**
   ```
   User → FastAPI → JWT Token → Protected Routes
   ```

2. **Target Creation**
   ```
   User → API → MongoDB (MonitoringTarget) → Celery Task Queue
   ```

3. **Monitoring Cycle**
   ```
   Celery Beat → Scheduled Task → Celery Worker → Web Scraper
        ↓
   Content Extraction → Hash Comparison → Change Detection
        ↓
   AI Analysis (Gemini) → Email Notification → Database Update
   ```

4. **LinkedIn Monitoring Flow**
   ```
   LinkedIn Target → Selenium WebDriver → Content Scraping
        ↓
   Snapshot Creation → Content Hash → Comparison with Previous
        ↓
   Change Detected → AI Summary → User Notification
   ```

5. **Real-time Operations**
   ```
   Manual Check → API Endpoint → Immediate Celery Task
        ↓
   Background Processing → Live Results → User Feedback
   ```

### Key Architectural Patterns

- **Event-Driven Architecture**: Celery tasks for asynchronous processing
- **Repository Pattern**: Service layers abstracting database operations
- **Dependency Injection**: FastAPI's built-in DI for clean separation
- **Observer Pattern**: Change detection triggers notifications

## 🛠️ Tech Stack

- **Backend**: FastAPI (Python 3.13+)
- **Database**: MongoDB with Beanie ODM
- **Task Queue**: Celery with Redis
- **Web Scraping**: Selenium WebDriver, BeautifulSoup4
- **AI/ML**: Google Generative AI (Gemini)
- **Authentication**: JWT with PassLib
- **Email**: SMTP with aiosmtplib
- **Environment**: Pydantic Settings

## 📋 Prerequisites

- Python 3.13 or higher
- MongoDB database
- Redis server
- Chrome browser (for Selenium)
- ChromeDriver
- Google Gemini API key
- SMTP email account

## 🚀 Quick Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Fuwad13/Montoring-Agent.git
cd Montoring-Agent
```

### 2. Install Dependencies

```bash
uv sync
```

### 3. Environment Configuration

Create a `.env` file in the root directory:

```env
# Database
MONGODB_URI=mongodb://localhost:27017/monitoring_agent

# LinkedIn Credentials
LNKDIN_EMAIL=your_linkedin_email@example.com
LNKDIN_PASSWORD=your_linkedin_password

# AI Configuration
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.0-flash
GEMINI_TEMPERATURE=0.1

# Authentication
JWT_SECRET_KEY=your_secret_key_here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
EMAIL_FROM=your_email@gmail.com
EMAIL_FROM_NAME=Monitoring Agent

# Redis
REDIS_URL=redis://localhost:6379/0

# Chrome Driver (adjust path as needed)
CHROME_DRIVER_PATH=./chromedriver.exe
```

### 4. Start Services

**Terminal 1 - Start the API Server:**
```bash
fastapi dev app
```

**Terminal 2 - Start Celery Worker:**
```bash
celery -A app.worker.celery_app worker --loglevel=info
```

**Terminal 3 - Start Celery Beat (Scheduler):**
```bash
celery -A app.beat.celery_app beat --loglevel=info
```

### 5. Access the Application

- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

## 📁 Project Structure

```
Montoring-Agent/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── worker.py              # Celery worker entry point
│   ├── beat.py                # Celery beat scheduler entry point
│   │
│   ├── api/                   # API layer
│   │   └── v1/
│   │       └── routes/
│   │           ├── auth.py    # Authentication endpoints
│   │           ├── monitoring.py  # Monitoring endpoints
│   │           └── user.py    # User management endpoints
│   │
│   ├── core/                  # Core application modules
│   │   ├── celery_app.py     # Celery configuration
│   │   ├── config.py         # Application settings
│   │   ├── db.py             # Database connection
│   │   └── log/
│   │       └── logger.py     # Logging configuration
│   │
│   └── modules/               # Business logic modules
│       ├── auth/              # Authentication module
│       │   ├── dependencies.py
│       │   ├── models.py
│       │   └── services.py
│       │
│       ├── monitoring/        # Core monitoring functionality
│       │   ├── agents.py      # Monitoring agents
│       │   ├── ai_service.py  # AI analysis service
│       │   ├── email_service.py # Email notifications
│       │   ├── linkedin_service.py # LinkedIn scraping
│       │   ├── models.py      # Data models
│       │   ├── scraper.py     # Web scraping utilities
│       │   ├── services.py    # Business logic
│       │   └── tasks.py       # Celery tasks
│       │
│       └── user/              # User management
│           ├── models.py
│           └── services.py
│
├── debug_html/               # Debug output storage
├── pyproject.toml           # Project dependencies
├── lnkdin_cookies.txt       # LinkedIn session cookies
└── README.md               # This file
```

## 📚 API Usage Examples

### Authentication

**Register a new user:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "secure_password",
    "full_name": "John Doe"
  }'
```

**Login:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "secure_password"
  }'
```

### Monitoring Management

**Add a LinkedIn profile to monitor:**
```bash
curl -X POST "http://localhost:8000/api/v1/monitoring/targets" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.linkedin.com/in/example-profile",
    "target_type": "linkedin_profile",
    "check_frequency": 3600
  }'
```

**Get monitoring targets:**
```bash
curl -X GET "http://localhost:8000/api/v1/monitoring/targets" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Get detected changes:**
```bash
curl -X GET "http://localhost:8000/api/v1/monitoring/changes" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Trigger manual check:**
```bash
curl -X POST "http://localhost:8000/api/v1/monitoring/targets/{target_id}/check" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Monitoring Target Types

- `linkedin_profile` - Monitor LinkedIn personal profiles
- `linkedin_company` - Monitor LinkedIn company pages  
- `website` - Monitor general websites

## 🔧 Configuration

### Check Frequencies

Configure how often targets are monitored:
- **3600** - Every hour (default)
- **1800** - Every 30 minutes
- **86400** - Daily
- Custom values in seconds

### Email Templates

Email notifications include:
- Target URL and type
- Change summary generated by AI
- Timestamp of detection
- Direct links to view full changes

### AI Analysis

The system uses Google Gemini to:
- Analyze content changes
- Generate human-readable summaries
- Identify significant updates
- Filter out minor formatting changes

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.