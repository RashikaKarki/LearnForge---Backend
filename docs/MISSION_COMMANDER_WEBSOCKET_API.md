# Mission Commander WebSocket API - Frontend Integration Guide

Complete guide for integrating the Mission Commander WebSocket endpoint into your frontend application.

## Table of Contents
- [Quick Start](#quick-start)
- [Connection Setup](#connection-setup)
- [Message Protocol](#message-protocol)
- [Code Examples](#code-examples)
- [Error Handling](#error-handling)
- [Testing](#testing)
- [Production Deployment](#production-deployment)
- [Integration Checklist](#integration-checklist)

---

## Quick Start

### Step 1: Create a Session

Before connecting to the WebSocket, you must create a session to get a `session_id`:

```javascript
// POST /api/v1/sessions
const response = await fetch('http://localhost:8000/api/v1/sessions', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${firebaseToken}`
  }
});

const { session_id, user_id } = await response.json();
// session_id: "abc123def456"
// user_id: "user123"
```

### Step 2: Connect to WebSocket

Use the `session_id` from Step 1:

**Endpoint:** `ws://localhost:8000/api/v1/mission-commander/ws`

**Required Query Parameters:**
- `session_id`: From the `/api/v1/sessions` endpoint
- `token`: Firebase authentication token

```javascript
const ws = new WebSocket(
  `ws://localhost:8000/api/v1/mission-commander/ws?session_id=${session_id}&token=${firebaseToken}`
);
```

---

## Connection Setup

### JavaScript/TypeScript

```typescript
class MissionCommanderClient {
  private ws: WebSocket | null = null;
  private sessionId: string = '';

  async connect(firebaseToken: string) {
    // Step 1: Create session
    const response = await fetch('http://localhost:8000/api/v1/sessions', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${firebaseToken}` }
    });
    const { session_id } = await response.json();
    this.sessionId = session_id;
    
    // Step 2: Connect WebSocket
    const wsUrl = `ws://localhost:8000/api/v1/mission-commander/ws?session_id=${session_id}&token=${firebaseToken}`;
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => console.log('Connected');
    this.ws.onmessage = (event) => this.handleMessage(JSON.parse(event.data));
    this.ws.onerror = (error) => console.error('Error:', error);
    this.ws.onclose = () => console.log('Disconnected');
  }

  private handleMessage(data: any) {
    switch (data.type) {
      case 'connected':
        console.log('Session started');
        break;
      case 'agent_message':
        this.displayAgentMessage(data.content);
        break;
      case 'mission_created':
        this.displayMission(data.mission);
        this.disconnect();
        break;
      case 'error':
        this.displayError(data.message);
        break;
    }
  }

  sendMessage(content: string) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'user_message',
        content: content
      }));
    }
  }

  disconnect() {
    this.ws?.close();
    this.ws = null;
  }
}
```

---

## Message Protocol

### Messages You Send (Client → Server)

#### 1. User Message
```javascript
{
  "type": "user_message",
  "content": "I want to learn Python for data analysis"
}
```

#### 2. Heartbeat (Optional)
```javascript
{
  "type": "ping"
}
```

### Messages You Receive (Server → Client)

#### 1. Connection Confirmation
```javascript
{
  "type": "connected",
  "message": "Connected to Mission Commander. Starting your learning journey..."
}
```

#### 2. Agent Response
```javascript
{
  "type": "agent_message",
  "content": "Great! What's your main motivation for learning Python?"
}
```

#### 3. Mission Created (Final Message)
```javascript
{
  "type": "mission_created",
  "message": "Mission created successfully!",
  "mission": {
    "id": "abc123",
    "title": "Python for Data Analysis",
    "short_description": "Learn Python fundamentals and data analysis",
    "description": "This mission guides you through Python basics...",
    "level": "Beginner",
    "topics_to_cover": [
      "Python Basics",
      "Variables and Data Types",
      "Working with Pandas",
      "Data Visualization"
    ],
    "learning_goal": "Master Python for analyzing spreadsheet data",
    "byte_size_checkpoints": [
      "Introduction to Python Programming",
      "Variables, Data Types, and Basic Operations",
      "Control Flow and Functions",
      "Introduction to Pandas for Data Analysis",
      "Data Visualization with Matplotlib",
      "Final Project: Analyzing Real-World Data"
    ],
    "skills": ["Python", "Data Analysis", "Pandas"],
    "creator_id": "user123",
    "is_public": true,
    "created_at": "2025-10-25T10:30:00Z",
    "updated_at": "2025-10-25T10:30:00Z"
  },
  "enrollment": {
    "id": "user123_abc123",
    "user_id": "user123",
    "mission_id": "abc123",
    "enrolled_at": "2025-10-25T10:30:00Z",
    "progress": 0.0,
    "last_accessed_at": "2025-10-25T10:30:00Z",
    "completed": false,
    "created_at": "2025-10-25T10:30:00Z",
    "updated_at": "2025-10-25T10:30:00Z"
  }
}
```

#### 4. Error
```javascript
{
  "type": "error",
  "message": "Error description"
}
```

#### 5. Pong Response
```javascript
{
  "type": "pong"
}
```

---

## Code Examples

### React Integration

```tsx
import { useState, useEffect, useRef } from 'react';

interface Message {
  from: 'user' | 'agent' | 'system';
  text: string;
}

interface Mission {
  id: string;
  title: string;
  short_description: string;
  byte_size_checkpoints: string[];
  level: string;
}

export function MissionCommanderChat({ firebaseToken }: { firebaseToken: string }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [mission, setMission] = useState<Mission | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    let ws: WebSocket;

    async function initializeConnection() {
      try {
        // Step 1: Create session
        const response = await fetch('http://localhost:8000/api/v1/sessions', {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${firebaseToken}` }
        });
        const { session_id } = await response.json();

        // Step 2: Connect to WebSocket
        ws = new WebSocket(
          `ws://localhost:8000/api/v1/mission-commander/ws?session_id=${session_id}&token=${firebaseToken}`
        );
        wsRef.current = ws;

        ws.onopen = () => setIsConnected(true);

        ws.onmessage = (event) => {
          const data = JSON.parse(event.data);
          setIsLoading(false);

          switch (data.type) {
            case 'connected':
              setMessages(prev => [...prev, { from: 'system', text: data.message }]);
              break;
            case 'agent_message':
              setMessages(prev => [...prev, { from: 'agent', text: data.content }]);
              break;
            case 'mission_created':
              setMission(data.mission);
              setMessages(prev => [...prev, { from: 'system', text: data.message }]);
              break;
            case 'error':
              setMessages(prev => [...prev, { from: 'system', text: `Error: ${data.message}` }]);
              break;
          }
        };

        ws.onerror = () => setIsConnected(false);
        ws.onclose = () => setIsConnected(false);
      } catch (error) {
        console.error('Connection failed:', error);
      }
    }

    initializeConnection();

    return () => ws?.close();
  }, [firebaseToken]);

  const sendMessage = () => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN || !input.trim()) {
      return;
    }

    wsRef.current.send(JSON.stringify({
      type: 'user_message',
      content: input
    }));

    setMessages(prev => [...prev, { from: 'user', text: input }]);
    setInput('');
    setIsLoading(true);
  };

  if (mission) {
    return (
      <div className="mission-created">
        <h2>🎉 Mission Created!</h2>
        <h3>{mission.title}</h3>
        <p>{mission.short_description}</p>
        <div className="mission-details">
          <p><strong>Level:</strong> {mission.level}</p>
          <p><strong>Checkpoints:</strong></p>
          <ul>
            {mission.byte_size_checkpoints.map((checkpoint, i) => (
              <li key={i}>{checkpoint}</li>
            ))}
          </ul>
        </div>
        <button onClick={() => window.location.href = `/missions/${mission.id}`}>
          Start Mission
        </button>
      </div>
    );
  }

  return (
    <div className="chat-container">
      <div className="connection-status">
        {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
      </div>

      <div className="messages">
        {messages.map((msg, i) => (
          <div key={i} className={`message message-${msg.from}`}>
            <div className="message-content">{msg.text}</div>
          </div>
        ))}
        {isLoading && <div className="typing-indicator">Agent is typing...</div>}
      </div>

      <div className="input-area">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
          placeholder="Type your message..."
          disabled={!isConnected || isLoading}
        />
        <button 
          onClick={sendMessage} 
          disabled={!isConnected || isLoading || !input.trim()}
        >
          Send
        </button>
      </div>
    </div>
  );
}
```

### Vanilla JavaScript

```javascript
class MissionChat {
  constructor(firebaseToken) {
    this.firebaseToken = firebaseToken;
    this.ws = null;
    this.messages = [];
  }

  async connect() {
    // Create session
    const response = await fetch('http://localhost:8000/api/v1/sessions', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${this.firebaseToken}` }
    });
    const { session_id } = await response.json();

    // Connect WebSocket
    this.ws = new WebSocket(
      `ws://localhost:8000/api/v1/mission-commander/ws?session_id=${session_id}&token=${this.firebaseToken}`
    );

    this.ws.onopen = () => this.onConnected();
    this.ws.onmessage = (event) => this.onMessage(JSON.parse(event.data));
    this.ws.onerror = (error) => this.onError(error);
    this.ws.onclose = () => this.onDisconnected();
  }

  onConnected() {
    console.log('Connected to Mission Commander');
    this.updateUI('connected');
  }

  onMessage(data) {
    switch (data.type) {
      case 'agent_message':
        this.addMessage('agent', data.content);
        break;
      case 'mission_created':
        this.showMission(data.mission);
        break;
      case 'error':
        this.showError(data.message);
        break;
    }
  }

  sendMessage(text) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'user_message',
        content: text
      }));
      this.addMessage('user', text);
    }
  }

  addMessage(from, text) {
    this.messages.push({ from, text });
    this.renderMessages();
  }

  showMission(mission) {
    document.getElementById('chat').style.display = 'none';
    document.getElementById('mission-result').innerHTML = `
      <h2>${mission.title}</h2>
      <p>${mission.short_description}</p>
      <a href="/missions/${mission.id}">Start Mission</a>
    `;
  }

  renderMessages() {
    const container = document.getElementById('messages');
    container.innerHTML = this.messages.map(msg => `
      <div class="message message-${msg.from}">
        ${msg.text}
      </div>
    `).join('');
    container.scrollTop = container.scrollHeight;
  }
}

// Usage
const chat = new MissionChat('firebase-token-here');
chat.connect();

// Send message
document.getElementById('send-btn').onclick = () => {
  const input = document.getElementById('message-input');
  chat.sendMessage(input.value);
  input.value = '';
};
```

### Python Client

```python
import asyncio
import json
import websockets
import aiohttp

async def create_session(firebase_token: str) -> str:
    """Create a session and return session_id"""
    async with aiohttp.ClientSession() as session:
        async with session.post(
            'http://localhost:8000/api/v1/sessions',
            headers={'Authorization': f'Bearer {firebase_token}'}
        ) as response:
            data = await response.json()
            return data['session_id']

async def mission_commander_chat(firebase_token: str):
    # Step 1: Create session
    session_id = await create_session(firebase_token)
    
    # Step 2: Connect to WebSocket
    uri = f"ws://localhost:8000/api/v1/mission-commander/ws?session_id={session_id}&token={firebase_token}"
    
    async with websockets.connect(uri) as websocket:
        # Receive connection confirmation
        response = await websocket.recv()
        data = json.loads(response)
        print(f"System: {data['message']}")
        
        # Conversation loop
        while True:
            # Get user input
            user_input = input("You: ")
            
            # Send message
            await websocket.send(json.dumps({
                "type": "user_message",
                "content": user_input
            }))
            
            # Receive response
            response = await websocket.recv()
            data = json.loads(response)
            
            if data["type"] == "agent_message":
                print(f"Agent: {data['content']}")
                
            elif data["type"] == "mission_created":
                print("\n🎉 Mission Created!")
                print(f"Title: {data['mission']['title']}")
                print(f"ID: {data['mission']['id']}")
                print(f"\nCheckpoints:")
                for i, checkpoint in enumerate(data['mission']['byte_size_checkpoints'], 1):
                    print(f"  {i}. {checkpoint}")
                break
                
            elif data["type"] == "error":
                print(f"❌ Error: {data['message']}")
                break

# Run
asyncio.run(mission_commander_chat("your-firebase-token"))
```

---

## Error Handling

### Connection Errors

```javascript
class ResilientClient {
  constructor(firebaseToken) {
    this.firebaseToken = firebaseToken;
    this.maxRetries = 3;
    this.retryDelay = 2000;
    this.retryCount = 0;
  }

  async connectWithRetry() {
    try {
      await this.connect();
      this.retryCount = 0; // Reset on success
    } catch (error) {
      if (this.retryCount < this.maxRetries) {
        this.retryCount++;
        console.log(`Retrying in ${this.retryDelay}ms... (${this.retryCount}/${this.maxRetries})`);
        await new Promise(resolve => setTimeout(resolve, this.retryDelay));
        this.retryDelay *= 2; // Exponential backoff
        return this.connectWithRetry();
      }
      throw new Error('Max retries reached');
    }
  }

  async connect() {
    // Session creation
    const response = await fetch('http://localhost:8000/api/v1/sessions', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${this.firebaseToken}` }
    });

    if (!response.ok) {
      throw new Error(`Session creation failed: ${response.status}`);
    }

    const { session_id } = await response.json();

    // WebSocket connection
    return new Promise((resolve, reject) => {
      const ws = new WebSocket(
        `ws://localhost:8000/api/v1/mission-commander/ws?session_id=${session_id}&token=${this.firebaseToken}`
      );

      ws.onopen = () => resolve(ws);
      ws.onerror = (error) => reject(error);
      
      setTimeout(() => reject(new Error('Connection timeout')), 10000);
    });
  }
}
```

### Common Error Scenarios

| Error | Cause | Solution |
|-------|-------|----------|
| `Connection Refused` | Server not running | Check server status, verify port 8000 |
| `1008 Policy Violation` | Missing/invalid session | Verify session was created successfully |
| `1008 Policy Violation` | Inactive session | Session already used, create new session |
| `Invalid token` | Expired Firebase token | Refresh authentication token |
| `Network timeout` | Slow connection | Implement retry with backoff |
| `Agent error` | Processing failure | Display error, allow retry |

### Error Handling UI

```tsx
function ChatWithErrorHandling() {
  const [error, setError] = useState<string | null>(null);
  const [retrying, setRetrying] = useState(false);

  const handleError = (errorMessage: string) => {
    setError(errorMessage);
    setRetrying(false);
  };

  const retry = async () => {
    setError(null);
    setRetrying(true);
    try {
      await connectToWebSocket();
    } catch (e) {
      handleError('Unable to connect. Please try again.');
    }
  };

  return (
    <div>
      {error && (
        <div className="error-banner">
          <p>{error}</p>
          <button onClick={retry} disabled={retrying}>
            {retrying ? 'Retrying...' : 'Try Again'}
          </button>
        </div>
      )}
      {/* Chat UI */}
    </div>
  );
}
```

---

## Testing

### Manual Testing with wscat

Install wscat:
```bash
npm install -g wscat
```

Create a session first:
```bash
curl -X POST http://localhost:8000/api/v1/sessions \
  -H "Authorization: Bearer test-token"
# Response: {"session_id": "abc123", "user_id": "user123"}
```

Connect to WebSocket:
```bash
wscat -c "ws://localhost:8000/api/v1/mission-commander/ws?session_id=abc123&token=test-token"
```

Send test message:
```json
{"type": "user_message", "content": "I want to learn Python"}
```

### Test Conversation Flow

A complete conversation typically follows this pattern:

```
1. Connect → Receive "connected"
2. Send: "I want to learn Python for data analysis"
   Receive: "What's your main motivation?"
3. Send: "I want to analyze business data"
   Receive: "Do you have programming experience?"
4. Send: "No, I'm a complete beginner"
   Receive: "How much time can you dedicate weekly?"
5. Send: "About 5 hours per week"
   Receive: Agent summarizes learning goals
6. Send: "Yes, that's correct"
   Receive: "mission_created" with full mission JSON
7. Connection closes
```

### Automated Testing Example

```javascript
// Jest test example
describe('MissionCommanderClient', () => {
  it('should create session and connect', async () => {
    const client = new MissionCommanderClient();
    
    global.fetch = jest.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ session_id: 'test123', user_id: 'user123' })
      })
    );

    global.WebSocket = jest.fn(() => ({
      readyState: WebSocket.OPEN,
      send: jest.fn(),
      close: jest.fn(),
      onopen: null,
      onmessage: null,
      onerror: null,
      onclose: null
    }));

    await client.connect('test-token');
    
    expect(fetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/sessions',
      expect.objectContaining({
        method: 'POST',
        headers: { 'Authorization': 'Bearer test-token' }
      })
    );
  });
});
```

---

## Production Deployment

### Environment Configuration

```javascript
// config.js
const config = {
  development: {
    apiUrl: 'http://localhost:8000',
    wsUrl: 'ws://localhost:8000'
  },
  production: {
    apiUrl: 'https://api.yourdomain.com',
    wsUrl: 'wss://api.yourdomain.com'
  }
};

export const getConfig = () => {
  const env = process.env.NODE_ENV || 'development';
  return config[env];
};

// Usage
const { apiUrl, wsUrl } = getConfig();
const wsConnection = `${wsUrl}/api/v1/mission-commander/ws?session_id=${sessionId}&token=${token}`;
```

### Security Checklist

- ✅ **Use WSS (wss://)** in production, not WS (ws://)
- ✅ **Validate Firebase tokens** server-side
- ✅ **Implement rate limiting** per user/session
- ✅ **Enable CORS** with specific origins only
- ✅ **Set session timeouts** to prevent resource leaks
- ✅ **Sanitize user input** before sending
- ✅ **Never log** sensitive data (tokens, PII)
- ✅ **Implement HTTPS** for session creation endpoint

### Performance Optimization

```javascript
// Implement heartbeat to keep connection alive
class MissionCommanderClient {
  private heartbeatInterval: NodeJS.Timer | null = null;

  connect() {
    // ... connection code ...
    
    // Start heartbeat (every 30 seconds)
    this.heartbeatInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000);
  }

  disconnect() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
    }
    this.ws?.close();
  }
}
```

### Cloud Run Configuration

If deploying to Google Cloud Run:

```yaml
# cloud-run.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: mission-commander
spec:
  template:
    spec:
      containerConcurrency: 80
      timeoutSeconds: 3600  # 1 hour for long conversations
      containers:
      - image: gcr.io/your-project/mission-commander
        env:
        - name: PORT
          value: "8080"
        - name: ALLOW_ORIGINS
          value: "https://yourdomain.com"
```

---

## Integration Checklist

### Pre-Integration
- [ ] Review this documentation
- [ ] Backend server running and accessible
- [ ] Valid Firebase authentication setup
- [ ] User authentication working (have user_id and token)

### Basic Implementation
- [ ] Session creation endpoint integrated
- [ ] WebSocket connection established
- [ ] Message sending implemented
- [ ] Message receiving and parsing implemented
- [ ] All message types handled (connected, agent_message, mission_created, error)

### UI Components
- [ ] Chat interface with message display
- [ ] User input field with send button
- [ ] Mission result display
- [ ] Connection status indicator
- [ ] Loading/typing indicators
- [ ] Error display with retry option

### Error Handling
- [ ] Connection errors caught and handled
- [ ] Authentication errors handled
- [ ] Network timeouts handled
- [ ] Retry logic with exponential backoff
- [ ] User-friendly error messages

### User Experience
- [ ] Messages display in real-time
- [ ] Auto-scroll to latest message
- [ ] Disable input while waiting for response
- [ ] Clear feedback on connection status
- [ ] Graceful handling of disconnections
- [ ] Navigation to mission page after creation

### Testing
- [ ] Manual testing with wscat
- [ ] Test successful conversation flow
- [ ] Test error scenarios
- [ ] Test on multiple browsers
- [ ] Test on mobile devices
- [ ] Test with slow network (throttling)

### Production Ready
- [ ] Use WSS (wss://) for secure connections
- [ ] Environment-based configuration
- [ ] Proper error tracking (Sentry, etc.)
- [ ] Analytics integration
- [ ] Performance monitoring
- [ ] Accessibility (ARIA labels, keyboard navigation)

---

## Typical Conversation Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. User Opens Chat Interface                                │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Create Session (POST /api/v1/sessions)                   │
│    → Receive session_id                                      │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Connect WebSocket                                         │
│    → Receive "connected" message                             │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. User sends: "I want to learn Python"                     │
│    → Agent asks: "What's your goal?"                         │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. User answers questions                                    │
│    → Agent continues gathering requirements                  │
│    → Multiple back-and-forth exchanges                       │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Agent summarizes learning plan                            │
│    User confirms: "Yes, that's correct"                      │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. Receive "mission_created" message                         │
│    → Full mission object with checkpoints                    │
│    → Display mission to user                                 │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 8. Connection Closes                                         │
│    → Navigate to mission page (/missions/{id})              │
└─────────────────────────────────────────────────────────────┘
```

---

## Advanced Features

### Session Persistence (Future Enhancement)

```javascript
// Save conversation history
class PersistentMissionChat {
  saveConversation(sessionId, messages) {
    localStorage.setItem(`conversation_${sessionId}`, JSON.stringify(messages));
  }

  loadConversation(sessionId) {
    const saved = localStorage.getItem(`conversation_${sessionId}`);
    return saved ? JSON.parse(saved) : [];
  }

  resumeSession(sessionId) {
    const messages = this.loadConversation(sessionId);
    // Display previous messages
    // Reconnect to same session (requires backend support)
  }
}
```

### Typing Indicators

```javascript
// Simulate typing indicator
onMessage(data) {
  if (data.type === 'agent_message') {
    this.showTypingIndicator();
    
    // Simulate word-by-word display
    const words = data.content.split(' ');
    let currentText = '';
    
    words.forEach((word, index) => {
      setTimeout(() => {
        currentText += (index > 0 ? ' ' : '') + word;
        this.updateLastMessage(currentText);
      }, index * 100);
    });
  }
}
```

### Export Conversation

```javascript
exportConversation() {
  const text = this.messages.map(msg => 
    `${msg.from === 'user' ? 'You' : 'Agent'}: ${msg.text}`
  ).join('\n\n');
  
  const blob = new Blob([text], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `mission-conversation-${Date.now()}.txt`;
  a.click();
}
```

---

## Troubleshooting

### Connection won't establish
**Symptoms:** WebSocket connection fails immediately

**Check:**
1. Is the server running? `curl http://localhost:8000/health`
2. Did session creation succeed? Check response has `session_id`
3. Is the session ID being passed correctly in the URL?
4. Is the Firebase token valid and not expired?
5. Check browser console for WebSocket errors

### No response from agent
**Symptoms:** User sends message but receives no reply

**Check:**
1. Is the message format correct? Must be valid JSON with `type: "user_message"`
2. Check server logs for errors
3. Verify WebSocket connection is still open (`ws.readyState === 1`)
4. Try sending a simple test message: `{"type": "user_message", "content": "test"}`

### Mission not created
**Symptoms:** Conversation ends but no mission received

**Check:**
1. Did you confirm the learning goal when asked?
2. Look for `mission_created` message type in received messages
3. Check server logs for mission creation errors
4. Verify conversation reached natural completion
5. Check Firestore console for newly created mission

### Connection drops frequently
**Symptoms:** WebSocket disconnects unexpectedly

**Solutions:**
1. Implement heartbeat with ping/pong (every 30s)
2. Add automatic reconnection with exponential backoff
3. Check network stability
4. Increase timeout on Cloud Run if deployed there
5. Monitor for memory leaks in long-running connections

---

## Support Resources

- **Backend Repository:** Check README.md for server setup
- **Test Script:** `/backend/test_websocket.py` for automated testing
- **API Health Check:** `GET /health` endpoint
- **Firebase Setup:** See firebase configuration docs

---

## Next Steps After Integration

Once you receive the `mission_created` message:

1. **Store Mission ID:** Save `mission.id` for future reference
2. **Navigate User:** Redirect to `/missions/{mission.id}`
3. **Display Mission:** Show title, description, checkpoints
4. **Enable Start:** Button to begin first checkpoint
5. **Track Progress:** Implement checkpoint completion tracking
6. **Share Feature:** Allow users to share their mission

---

**Questions or issues?** Check server logs, test with wscat, and verify all authentication tokens are valid. Most connection issues are due to invalid/expired Firebase tokens or missing session creation step.
