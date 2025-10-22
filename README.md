# LearnForge: A Personalized AI Learning Architect

## Introduction

**LearnForge** is an AI-powered educational backend that designs and orchestrates deeply personalized learning experiences. Built with the **Agent Development Kit (ADK)** and powered by a **multi-agent architecture**, LearnForge adapts to each learner’s goals, existing knowledge, and preferred depth of understanding.

It intelligently generates **missions**, **content**, and **evaluations** — guiding users through an adaptive journey toward true mastery.


## Core Principles

* **Personalization** – Learning paths are dynamically tailored to the learner’s objectives, desired depth, and prior experience.
* **Byte-Sized Learning** – Every concept is delivered as a focused, digestible *mission* composed of smaller actionable *steps*.
* **Adaptive Reinforcement** – Continuous assessments and feedback ensure concept mastery through reinforcement and iteration.
* **Conversational Interface** – Learners interact naturally with AI agents that understand, guide, and support their progress.


## Getting Started

### Prerequisites

* Python ≥ 3.10
* [Poetry](https://python-poetry.org/docs/) installed

### Installation

```bash
# Clone the repository
git clone https://github.com/rashikakarki/learnforge-backend.git
cd learnforge-backend

# Install dependencies
poetry install

# Activate the virtual environment
poetry env activate
```

### Pre-commit hooks (linting & formatting)

This repository includes a `.pre-commit-config.yaml` that runs formatters and linters on each commit.

```bash
# run hooks once on all files
poetry run pre-commit run --all-files
```

### Run the Application

```bash
python main.py
```

By default, this starts the LearnForge backend service and initializes all AI agents.

## Tech Stack

* **Python** for backend logic
* **Agent Development Kit (ADK)** for multi-agent orchestration
* **Poetry** for dependency management and environment control
