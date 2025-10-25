# LearnForge: A Personalized AI Learning Architect

[![CI - Lint and Test](https://github.com/RashikaKarki/LearnForge---Backend/actions/workflows/ci.yml/badge.svg)](https://github.com/RashikaKarki/LearnForge---Backend/actions/workflows/ci.yml)
[![Deploy to Cloud Run](https://github.com/RashikaKarki/LearnForge---Backend/actions/workflows/deploy.yml/badge.svg)](https://github.com/RashikaKarki/LearnForge---Backend/actions/workflows/deploy.yml)

## Introduction

**LearnForge** is an AI-powered educational backend that designs and orchestrates deeply personalized learning experiences. Built with the **Agent Development Kit (ADK)** and powered by a **multi-agent architecture**, LearnForge adapts to each learner's goals, existing knowledge, and preferred depth of understanding.

It intelligently generates **missions**, **content**, and **evaluations** — guiding users through an adaptive journey toward true mastery.

## Core Principles

* **Personalization** – Learning paths are dynamically tailored to the learner's objectives, desired depth, and prior experience.
* **Byte-Sized Learning** – Every concept is delivered as a focused, digestible *mission* composed of smaller actionable *steps*.
* **Adaptive Reinforcement** – Continuous assessments and feedback ensure concept mastery through reinforcement and iteration.
* **Conversational Interface** – Learners interact naturally with AI agents that understand, guide, and support their progress.

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
| `firebase-service-account-key` | Firebase service account JSON | Upload `firebase_key.json` |
| `google-api-key` | Google API key for Gemini/GenAI | Paste API key value |
| `allow-origins` | CORS allowed origins | e.g., `https://myapp.com,http://localhost:8000` |

**Important:** Grant Cloud Run service account access to these secrets:

```bash
# Get your project number
PROJECT_NUMBER=$(gcloud projects describe YOUR_PROJECT_ID --format='value(projectNumber)')

# Grant access to all secrets
for SECRET in firebase-service-account-key google-api-key allow-origins; do
  gcloud secrets add-iam-policy-binding $SECRET \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
done
```

Or use the Console:
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

* **Python 3.11** - Backend runtime
* **FastAPI** - Web framework
* **Agent Development Kit (ADK)** - Multi-agent orchestration
* **FireBase** - Authentication
* **Google Firestore** - Database
* **Docker** - Containerization
* **Google Cloud Run** - Production deployment

## Documentation

- [unit_testing_guide.md](unit_testing_guide.md) - Testing guide
