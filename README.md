# LearnForge: A Personalized AI Learning Architect

[![CI - Lint and Test](https://github.com/RashikaKarki/LearnForge---Backend/actions/workflows/ci.yml/badge.svg)](https://github.com/RashikaKarki/LearnForge---Backend/actions/workflows/ci.yml)
[![Deploy to Cloud Run](https://github.com/RashikaKarki/LearnForge---Backend/actions/workflows/deploy.yml/badge.svg)](https://github.com/RashikaKarki/LearnForge---Backend/actions/workflows/deploy.yml)

## Introduction

**LearnForge** is an intelligent, AI-driven learning platform that transforms how people learn by providing deeply personalized, adaptive educational experiences. Built entirely on Google Cloud infrastructure and powered by Google's Agent Development Kit (ADK) with Gemini 2.5 Flash, LearnForge guides learners from vague interests to mastery through two sophisticated AI agents: **Polaris** and **Lumina**.

LearnForge doesn't just deliver content—it creates a complete learning journey. The system understands each learner's goals, experience level, and preferred learning style, then dynamically generates structured learning missions, delivers personalized content, and adapts in real-time to ensure true comprehension and mastery.

## System Architecture

![LearnForge System Architecture](docs/architecture/architecture.png)

## Core Principles

* **Personalization** – Learning paths are dynamically tailored to the learner's objectives, desired depth, and prior experience.
* **Byte-Sized Learning** – Every concept is delivered as a focused, digestible *mission* composed of smaller actionable *checkpoints*.
* **Adaptive Reinforcement** – Continuous assessments and feedback ensure concept mastery through reinforcement and iteration.
* **Conversational Interface** – Learners interact naturally with AI agents that understand, guide, and support their progress.

## Agent Architecture

LearnForge uses two sophisticated AI agents:

### Polaris: The Pathfinder

![Polaris Architecture](docs/architecture/polaris_orchestrator.png)

- **Orchestrator Agent**: Manages agent transitions and coordinates mission creation flow
- **Pathfinder Agent (Polaris)**: Transforms vague learning interests into precise, actionable learning goals using Google Search for research-backed questions
- **Mission Curator Agent**: Converts collected data into structured mission schema with checkpoints and learning goals
- **Session Storage**: InMemorySessionService for ephemeral session storage

### Lumina: The Learning Companion

![Lumina Architecture](docs/architecture/lumina_architecture.png)

- **Lumina Orchestrator**: Coordinates learning journey through sequential checkpoints
- **Greeter Agent**: Provides initial welcome and mission introduction
- **Flow Briefer Agent**: Briefs user on upcoming checkpoint and confirms learning objectives
- **Sensei Agent**: Interactive teaching agent that presents content and evaluates understanding
- **Content Composer Agent**: Orchestrates content creation pipeline with Content Searcher, Video Selector (YouTube v3 API), and Content Formatter
- **Help Desk Agent**: Handles off-topic questions during missions using Google Search
- **Wrapper Agent**: Provides final mission wrap-up and celebration
- **Session Storage**: DatabaseSessionService with Cloud SQL (PostgreSQL) for persistent session storage

## Prerequisites

* Docker & Docker Compose
* Google Cloud SDK (for deployment)

## Quick Start

```bash
# Clone the repository
git clone https://github.com/rashikakarki/learnforge-backend.git
cd learnforge-backend

# Create .env file
cp .env.example .env
# Edit .env and add your configuration

# Start the application
make up
```

The API will be available at http://localhost:8080

## Available Commands

### Development

```bash
make up              # Start development server
make down            # Stop server
make logs            # View logs
make restart         # Restart server
make shell           # Open container shell
```

### Testing & Code Quality

```bash
make test            # Run all tests
make lint            # Run linters (ruff, black, isort)
make format          # Format code
make docker-test     # Test Docker build locally
```

### Deployment

```bash
make deploy          # Deploy to Google Cloud Run
```

> **Note**: Deployment requires `.env` file with GCP configuration and proper Google Cloud service account credentials.

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8080/docs
- **Health Check**: http://localhost:8080/api/health

### WebSocket Endpoints

- **Mission Commander (Polaris)**: `ws://localhost:8080/api/v1/mission-commander/ws`
  - Real-time AI agent conversation for creating personalized learning missions
  - Complete integration guide: [Mission Commander WebSocket API](docs/MISSION_COMMANDER_WEBSOCKET_API.md)

- **Mission Ally (Lumina)**: `ws://localhost:8080/api/v1/mission-ally/ws`
  - Real-time AI agent conversation for interactive learning through checkpoints
  - Complete integration guide: [Mission Ally WebSocket API](docs/MISSION_ALLY_WEBSOCKET_API.md)

## CI/CD Pipeline

### Automated Workflows

- **CI** - Runs on all branches and PRs
  - ✅ Linting (ruff, black, isort)
  - ✅ Unit tests (pytest)

- **CD** - Deploys on push to `main`
  - 🚀 Auto-deploy to Cloud Run

### Setup GitHub Deployment

#### 1. Create GitHub Secrets (Deployment Credentials)

Add these secrets in GitHub (Settings → Secrets and variables → Actions):

| Secret Name | Description | Example |
|------------|-------------|---------|
| `GCP_PROJECT_ID` | Your Google Cloud project ID | `my-project-123` |
| `GCP_REGION` | GCP region for deployment | `us-central1` |
| `GCP_SA_KEY` | Service account JSON key for deployment | `{"type": "service_account"...}` |
| `CLOUD_RUN_SERVICE` | Name of your Cloud Run service | `learnforge-backend` |
| `ARTIFACT_REGISTRY_REPO` | Artifact Registry repository name | `my-app-repo` |

#### 2. Create Google Cloud Secrets (Runtime Credentials)

These are used by your **running application** on Cloud Run. Create them in [Secret Manager](https://console.cloud.google.com/security/secret-manager):

| Secret Name | Description | How to Create |
|------------|-------------|---------------|
| `firebase-service-account-key` | Firebase service account JSON | Upload `firebase_key.json` content |
| `google-api-key` | Google API key for Gemini/GenAI | Paste API key value |
| `youtube-api-key` | YouTube Data API v3 key | Paste API key value |
| `allow-origins` | CORS allowed origins (comma-separated) | e.g., `https://myapp.com,https://app.myapp.com` ⚠️ **Never use `*` in production!** |
| `firestore-database-id` | Firestore database ID | e.g., `learnforge-staging` or `(default)` |
| `database-url` | Cloud SQL connection string (optional, if not using connector) | `postgresql://user:pass@host/db` |
| `instance-connection-name` | Cloud SQL instance connection name | `project:region:instance` |
| `db-user` | Cloud SQL database user | Database username |
| `db-password` | Cloud SQL database password | Database password |
| `db-name` | Cloud SQL database name | Database name |

**Important:** Grant Cloud Run service account access to these secrets.

1. Click on each secret → **PERMISSIONS** tab → **+ GRANT ACCESS**
2. Principal: `PROJECT_NUMBER-compute@developer.gserviceaccount.com`
3. Role: **Secret Manager Secret Accessor**

#### 3. Deploy

Ensure the Artifact Registry repository exists, then push to `main`:

```bash
# Create Artifact Registry repo (one-time setup)
gcloud artifacts repositories create YOUR_REPO_NAME \
    --repository-format=docker \
    --location=YOUR_REGION

# Deploy
git push origin main
```

## Credential Architecture

### Two Types of Credentials

**GitHub Secrets** (for CI/CD deployment):
- Used by GitHub Actions to **deploy** your app
- Service account needs: `roles/run.admin`, `roles/artifactregistry.writer`, `roles/iam.serviceAccountUser`

**Google Cloud Secrets** (for runtime):
- Used by your **running app** on Cloud Run
- Cloud Run service account needs: `roles/secretmanager.secretAccessor`

> **Key Point:** The service account that deploys your app is different from the one that runs it!


## Tech Stack

### Backend
* **Python 3.11** - Backend runtime
* **FastAPI** - Web framework
* **Agent Development Kit (ADK)** - Multi-agent orchestration framework
* **Gemini 2.5 Flash** - Large language model for agent intelligence

### Google Cloud Platform Services
* **Cloud Run** - Serverless container hosting for frontend and backend
* **Artifact Registry** - Container image storage and versioning
* **Cloud SQL (PostgreSQL)** - Managed database for session persistence (Lumina agent)
* **Cloud SQL Connector** - Secure database connection management
* **Firebase Authentication** - OAuth Google authentication
* **Firestore** - NoSQL database for user and mission data
* **Cloud Logging** - Centralized application logging
* **Cloud Trace** - Distributed tracing and performance monitoring
* **Secret Manager** - Secure credential storage

### External APIs
* **YouTube Data API v3** - Educational video search and curation
* **Google Search API** - Research-augmented content discovery

### Infrastructure
* **Docker** - Containerization

## Documentation

- [unit_testing_guide.md](coding_guidelines/unit_testing_guide.md) - Testing guide
