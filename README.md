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

1. Add GitHub secrets (Settings → Secrets and variables → Actions):
   
   **GCP Configuration:**
   - `GCP_PROJECT_ID` - Your Google Cloud project ID
   - `GCP_REGION` - The GCP region for deployment (e.g., us-central1)
   - `GCP_SA_KEY` - Service account JSON key with Cloud Run and Artifact Registry permissions
   
   **Cloud Run & Artifact Registry:**
   - `CLOUD_RUN_SERVICE` - Name of your Cloud Run service
   - `ARTIFACT_REGISTRY_REPO` - Name of your Artifact Registry repository
   
   **Application Configuration:**
   - `FIREBASE_PROJECT_ID` - Your Firebase project ID
   - `GOOGLE_API_KEY` - Google API key for Gemini/GenAI
   - `ALLOW_ORIGINS` - CORS allowed origins (comma-separated)

2. Ensure the Artifact Registry repository exists in GCP (must be created manually)

3. Push to `main` to deploy


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
