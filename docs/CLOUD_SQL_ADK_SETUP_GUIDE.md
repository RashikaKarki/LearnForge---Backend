# Quick Start: Build a Persistent AI Agent with Google ADK

Build a command-line AI agent that remembers conversations across sessions using Google's Agent Development Kit (ADK) and Cloud SQL.

## What You'll Build

A conversational AI agent that:
- 💬 Runs from your terminal
- 🧠 Remembers past conversations
- 🔄 Maintains context across sessions
- ☁️ Stores history in the cloud

**Time to complete:** 20-30 minutes

---

## Prerequisites

- Google Cloud account with billing enabled
- Python 3.11+ installed
- Basic terminal/command line knowledge

---

## Step 1: Set Up Your Google Cloud Project

### 1.1 Create a New Project

```bash
# Install gcloud CLI if you haven't
# Visit: https://cloud.google.com/sdk/docs/install

# Create and set project
gcloud projects create my-adk-agent --name="My ADK Agent"
gcloud config set project my-adk-agent

# Enable billing (required)
# Visit: https://console.cloud.google.com/billing
```

### 1.2 Enable Required APIs

```bash
# Enable all necessary APIs in one command
gcloud services enable \
  sqladmin.googleapis.com \
  sql-component.googleapis.com \
  compute.googleapis.com
```

**Why these APIs?**
- `sqladmin.googleapis.com` - Manages Cloud SQL connections
- `sql-component.googleapis.com` - Cloud SQL components
- `compute.googleapis.com` - Compute resources

---

## Step 2: Create Your Database

### 2.1 Create Cloud SQL Instance

```bash
# Create a small PostgreSQL instance (free tier eligible)
gcloud sql instances create my-agent-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1 \
  --root-password=CHANGE_ME_SECURE_PASSWORD
```

**This takes 5-10 minutes.** ☕ Grab a coffee!

### 2.2 Create Database and User

```bash
# Create the database
gcloud sql databases create agent_sessions \
  --instance=my-agent-db

# Create a user
gcloud sql users create agent_user \
  --instance=my-agent-db \
  --password=ANOTHER_SECURE_PASSWORD
```

### 2.3 Get Connection Details

```bash
# Get your connection name (save this!)
gcloud sql instances describe my-agent-db \
  --format="value(connectionName)"

# Example output: my-adk-agent:us-central1:my-agent-db
```

---

## Step 3: Set Up Service Account

### 3.1 Create Service Account

```bash
# Create service account
gcloud iam service-accounts create adk-agent \
  --display-name="ADK Agent Service Account"

# Get the email (save this!)
gcloud iam service-accounts list \
  --filter="displayName:ADK Agent Service Account" \
  --format="value(email)"
```

### 3.2 Grant Permissions

```bash
# Replace with your service account email
SERVICE_ACCOUNT="adk-agent@my-adk-agent.iam.gserviceaccount.com"
PROJECT_ID="my-adk-agent"

# Grant all three required Cloud SQL roles
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/cloudsql.client"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/cloudsql.editor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/cloudsql.instanceUser"
```

### 3.3 Create and Download Key

```bash
# Create key file
gcloud iam service-accounts keys create ~/adk-agent-key.json \
  --iam-account=$SERVICE_ACCOUNT

echo "✅ Key saved to ~/adk-agent-key.json"
```

---

## Step 4: Build Your Agent

### 4.1 Create Project Structure

```bash
# Create project directory
mkdir my-adk-agent && cd my-adk-agent

# Create file structure
mkdir -p agent
touch agent/__init__.py agent/my_agent.py
touch main.py requirements.txt .env
```

### 4.2 Install Dependencies

**File: `requirements.txt`**
```txt
google-genai
cloud-sql-python-connector[pg8000]
python-dotenv
```

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### 4.3 Configure Environment

**File: `.env`**
```bash
# Google Cloud
GOOGLE_APPLICATION_CREDENTIALS=/Users/your-username/adk-agent-key.json
GOOGLE_CLOUD_PROJECT=my-adk-agent

# Cloud SQL Connection
INSTANCE_CONNECTION_NAME=my-adk-agent:us-central1:my-agent-db
DB_USER=agent_user
DB_PASSWORD=ANOTHER_SECURE_PASSWORD
DB_NAME=agent_sessions

# Google AI API Key (get from https://aistudio.google.com/apikey)
GOOGLE_API_KEY=your_api_key_here
```

### 4.4 Create Your Agent

**File: `agent/my_agent.py`**
```python
"""A simple conversational agent with memory"""

from google import genai
from google.genai import types

# Initialize client
client = genai.Client()

def create_agent():
    """Create the root agent"""
    
    @client.agentic.agent(
        model="gemini-2.0-flash-exp",
        system_instruction="""
        You are a helpful AI assistant with a great memory.
        
        You remember previous conversations and can reference them.
        Be friendly, concise, and helpful.
        """,
    )
    def assistant_agent(request: str) -> str:
        """Main assistant that handles user requests"""
        return request
    
    return assistant_agent
```

**File: `main.py`**
```python
#!/usr/bin/env python3
"""Command-line interface for the ADK agent"""

import os
import sys
from dotenv import load_dotenv
from google.cloud.sql.connector import Connector
from google.adk.sessions import DatabaseSessionService
from google.adk.runners import Runner
from google.genai.types import Content, Part

from agent.my_agent import create_agent

# Load environment variables
load_dotenv()


def create_cloud_sql_connection():
    """Create Cloud SQL connection"""
    connector = Connector()
    return connector.connect(
        os.getenv("INSTANCE_CONNECTION_NAME"),
        "pg8000",
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        db=os.getenv("DB_NAME"),
    )


def main():
    print("🤖 ADK Agent Starting...\n")
    
    # Initialize session service with Cloud SQL
    print("📡 Connecting to database...")
    session_service = DatabaseSessionService(
        db_url="postgresql+pg8000://",
        creator=create_cloud_sql_connection,
    )
    print("✅ Connected!\n")
    
    # Create agent and runner
    agent = create_agent()
    runner = Runner(
        agent=agent,
        app_name="my-adk-agent",
        session_service=session_service,
    )
    
    # Get or create session
    user_id = "user_1"
    session_id = input("Enter session ID (or press Enter for new): ").strip()
    if not session_id:
        session_id = f"session_{os.urandom(4).hex()}"
        print(f"📝 Created new session: {session_id}\n")
    
    print(f"💬 Chat with your agent (type 'exit' to quit)\n")
    print("=" * 60)
    
    # Chat loop
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("\n👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            print("\nAgent: ", end="", flush=True)
            
            # Run agent
            for event in runner.run(
                user_id=user_id,
                session_id=session_id,
                new_message=Content(parts=[Part(text=user_input)])
            ):
                if hasattr(event, 'text'):
                    print(event.text, end="", flush=True)
            
            print()  # New line after response
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Continuing...")


if __name__ == "__main__":
    main()
```

---

## Step 5: Run Your Agent

### 5.1 Test the Connection

```bash
# Make sure you're in the virtual environment
source venv/bin/activate

# Test connection
python -c "
from dotenv import load_dotenv
import os
from google.cloud.sql.connector import Connector

load_dotenv()
connector = Connector()
conn = connector.connect(
    os.getenv('INSTANCE_CONNECTION_NAME'),
    'pg8000',
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    db=os.getenv('DB_NAME'),
)
print('✅ Database connection successful!')
conn.close()
connector.close()
"
```

### 5.2 Start Chatting!

```bash
python main.py
```

**Example session:**
```
🤖 ADK Agent Starting...

📡 Connecting to database...
✅ Connected!

Enter session ID (or press Enter for new): 
📝 Created new session: session_a3f8c92b

💬 Chat with your agent (type 'exit' to quit)

============================================================

You: Hi! My name is Alex and I love pizza.

Agent: Hello Alex! It's nice to meet you. Pizza is delicious! 
Do you have a favorite type of pizza?

You: exit

👋 Goodbye!
```

### 5.3 Test Memory Persistence

```bash
# Run again with the same session ID
python main.py

# Enter the session ID from before: session_a3f8c92b
```

**Example:**
```
You: Do you remember my name?

Agent: Yes! Your name is Alex, and you mentioned you love pizza!
```

**🎉 It remembers!** Your agent now has persistent memory across sessions.

---

## Common Issues & Solutions

### ❌ "Cloud SQL Admin API has not been used"

**Solution:**
```bash
gcloud services enable sqladmin.googleapis.com
# Wait 2-5 minutes, then try again
```

### ❌ "Permission denied" or "Access denied"

**Solution:** Verify all three roles are granted:
```bash
# Check your roles
gcloud projects get-iam-policy my-adk-agent \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:adk-agent@*"
```

You should see:
- `roles/cloudsql.client`
- `roles/cloudsql.editor`
- `roles/cloudsql.instanceUser`

### ❌ "ModuleNotFoundError: No module named 'google.cloud.sql'"

**Solution:**
```bash
pip install 'cloud-sql-python-connector[pg8000]'
```

### ❌ "File not found" (credentials error)

**Solution:** Check your `.env` file path:
```bash
# Make sure the path is absolute
GOOGLE_APPLICATION_CREDENTIALS=/full/path/to/adk-agent-key.json
```

---

## Next Steps

### Add More Features

**1. Multiple Users**
```python
# In main.py
user_id = input("Enter your username: ").strip()
```

**2. List Past Sessions**
```python
# Add before chat loop
sessions = runner.list_sessions(user_id=user_id)
print(f"Your sessions: {[s.session_id for s in sessions]}")
```

**3. Better Prompts**
```python
# In agent/my_agent.py
system_instruction="""
You are an expert assistant specialized in [YOUR DOMAIN].

Context: You have access to conversation history.
Goal: Help users with [SPECIFIC TASKS].
Style: [Friendly/Professional/Technical]

Remember:
- Reference previous conversations when relevant
- Be concise but thorough
- Ask clarifying questions
"""
```

**4. Add Tools**
```python
from google.genai import types

@client.agentic.tool
def search_web(query: str) -> str:
    """Search the web for information"""
    # Add your search implementation
    return f"Search results for: {query}"

# Add to agent
@client.agentic.agent(
    model="gemini-2.0-flash-exp",
    system_instruction="...",
    tools=[search_web],  # Add tools here
)
def assistant_agent(request: str) -> str:
    return request
```

### Deploy to Production

**Option 1: Cloud Run (Recommended)**
- Convert to web service with FastAPI
- Use Secret Manager for credentials
- Enable automatic scaling

**Option 2: Compute Engine**
- Run as a long-lived service
- SSH access for debugging
- More control over environment

**Option 3: Cloud Functions**
- Serverless deployment
- Pay only for usage
- Great for low-traffic agents

---

## Cost Estimation

**Free Tier:**
- Cloud SQL: db-f1-micro (shared core, 614 MB RAM)
- Google AI: 1,500 requests/day free

**Estimated Monthly Cost (after free tier):**
- Cloud SQL: ~$7/month (if always running)
- API calls: ~$0.05 per 1,000 requests
- Storage: ~$0.17/GB/month

**💡 Cost-saving tips:**
- Stop Cloud SQL instance when not in use
- Use `db-f1-micro` for development
- Cache common responses
- Monitor usage in Cloud Console

---

## Resources

- 📚 [Google ADK Documentation](https://ai.google.dev/adk)
- 🔧 [Cloud SQL Best Practices](https://cloud.google.com/sql/docs/postgres/best-practices)
- 💬 [ADK Community Discord](https://discord.gg/google-ai)
- 📖 [Example Agents](https://github.com/google/agentic-py/tree/main/examples)

---

## Summary

You've built a production-ready AI agent with:
- ✅ Persistent conversation memory
- ✅ Cloud SQL database integration
- ✅ Command-line interface
- ✅ Session management
- ✅ Secure authentication

**What's powerful about this setup:**
- Your agent remembers context across sessions
- Conversations are stored securely in the cloud
- You can access chat history from anywhere
- It scales from prototype to production

**Next:** Try customizing the agent's personality, adding specialized tools, or deploying it as a web service!

