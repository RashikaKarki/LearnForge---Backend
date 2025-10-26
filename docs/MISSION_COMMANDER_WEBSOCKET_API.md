# Mission Commander WebSocket API

A conversational AI agent that guides users through creating personalized learning missions via WebSocket.

---

## Quick Start

### 1. Create Session
```bash
POST /api/v1/sessions
Authorization: Bearer {firebase_token}

Response:
{
  "session_id": "abc123",
  "user_id": "user456"
}
```

### 2. Connect WebSocket
```javascript
const ws = new WebSocket(
  `ws://localhost:8000/api/v1/mission-commander/ws?session_id=abc123&token={firebase_token}`
);
```

### 3. Handle Messages
```javascript
ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  
  switch (msg.type) {
    case 'connected':
      // Send first message to start conversation
      ws.send(JSON.stringify({
        type: 'user_message',
        message: 'Hello'
      }));
      break;
      
    case 'agent_message':
      displayMessage(msg.message);
      break;
      
    case 'mission_created':
      showMission(msg.mission);
      ws.close();
      break;
  }
};
```

---

## Message Types

### Client → Server

#### User Message
```json
{
  "type": "user_message",
  "message": "I want to learn Python for data analysis"
}
```

#### Ping (Keepalive)
```json
{
  "type": "ping"
}
```

### Server → Client

#### 1. Connected (First Message)
```json
{
  "type": "connected",
  "message": "Connected to Mission Commander. Starting your learning journey..."
}
```
**Action Required:** Send your first `user_message` to begin the conversation.

#### 2. Agent Message
```json
{
  "type": "agent_message",
  "message": "Hello! I'm your Mission Commander. What would you like to learn?"
}
```

#### 3. Agent Handover (Progress Update)
```json
{
  "type": "agent_handover",
  "agent": "mission_curator",
  "message": "Creating your personalized learning mission..."
}
```
**UI Tip:** Show loading indicator when this appears.

#### 4. Mission Created (Final Message)
```json
{
  "type": "mission_created",
  "message": "Mission created successfully!",
  "mission": {
    "id": "mission_123",
    "title": "Python for Data Analysis",
    "short_description": "Master Python fundamentals for data work",
    "description": "Complete guide to...",
    "level": "Beginner",
    "topics_to_cover": ["Python Basics", "Pandas", "Visualization"],
    "learning_goal": "Analyze data with Python",
    "byte_size_checkpoints": [
      "Python Fundamentals",
      "Working with Data",
      "Data Visualization"
    ],
    "skills": ["Python", "Data Analysis"],
    "creator_id": "user456",
    "is_public": true
  },
  "enrollment": {
    "id": "enroll_789",
    "user_id": "user456",
    "mission_id": "mission_123",
    "progress": 0.0,
    "completed": false
  }
}
```
**Next Step:** Navigate user to `/missions/{mission.id}`.

#### 5. Error
```json
{
  "type": "error",
  "message": "Error description"
}
```

#### 6. Pong
```json
{
  "type": "pong"
}
```

---

## Complete React Example

```tsx
import { useState, useEffect, useRef } from 'react';

interface Message {
  from: 'user' | 'agent' | 'system';
  text: string;
}

export function MissionChat({ firebaseToken }: { firebaseToken: string }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [mission, setMission] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    async function connect() {
      try {
        // Create session
        const res = await fetch('http://localhost:8000/api/v1/sessions', {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${firebaseToken}` }
        });
        const { session_id } = await res.json();

        // Connect WebSocket
        const ws = new WebSocket(
          `ws://localhost:8000/api/v1/mission-commander/ws?session_id=${session_id}&token=${firebaseToken}`
        );
        wsRef.current = ws;

        ws.onopen = () => setIsConnected(true);

        ws.onmessage = (event) => {
          const data = JSON.parse(event.data);
          setIsLoading(false);

          switch (data.type) {
            case 'connected':
              addMessage('system', data.message);
              // Start conversation
              ws.send(JSON.stringify({
                type: 'user_message',
                message: 'Hello'
              }));
              setIsLoading(true);
              break;

            case 'agent_message':
              addMessage('agent', data.message);
              break;

            case 'agent_handover':
              addMessage('system', `⚙️ ${data.message}`);
              setIsLoading(true);
              break;

            case 'mission_created':
              setMission(data.mission);
              addMessage('system', '✅ ' + data.message);
              break;

            case 'error':
              addMessage('system', '❌ ' + data.message);
              break;
          }
        };

        ws.onerror = () => setIsConnected(false);
        ws.onclose = () => setIsConnected(false);
      } catch (error) {
        console.error('Connection failed:', error);
      }
    }

    connect();
    return () => wsRef.current?.close();
  }, [firebaseToken]);

  const addMessage = (from: 'user' | 'agent' | 'system', text: string) => {
    setMessages(prev => [...prev, { from, text }]);
  };

  const sendMessage = () => {
    if (!wsRef.current || !input.trim()) return;

    wsRef.current.send(JSON.stringify({
      type: 'user_message',
      message: input
    }));

    addMessage('user', input);
    setInput('');
    setIsLoading(true);
  };

  if (mission) {
    return (
      <div className="mission-result">
        <h2>🎉 Mission Created!</h2>
        <h3>{mission.title}</h3>
        <p>{mission.short_description}</p>
        <a href={`/missions/${mission.id}`}>Start Mission →</a>
      </div>
    );
  }

  return (
    <div className="chat">
      <div className="status">
        {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
      </div>

      <div className="messages">
        {messages.map((msg, i) => (
          <div key={i} className={`message message-${msg.from}`}>
            {msg.text}
          </div>
        ))}
        {isLoading && <div className="loading">Agent is thinking...</div>}
      </div>

      <div className="input">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
          placeholder="Type your message..."
          disabled={!isConnected || isLoading}
        />
        <button onClick={sendMessage} disabled={!isConnected || isLoading}>
          Send
        </button>
      </div>
    </div>
  );
}
```

---

## Conversation Flow

```
1. Connect → Receive "connected"
2. Send: "Hello" (first message required)
3. Receive: "What would you like to learn?"
4. Send: "I want to learn Python for data analysis"
5. Receive: "What's your main goal?"
6. Send: "Analyze business spreadsheets"
7. Receive: "Any programming experience?"
8. Send: "No, complete beginner"
9. Receive: "How much time weekly?"
10. Send: "5 hours per week"
11. Receive: Agent summarizes plan
12. Send: "Yes, that's perfect"
13. Receive: "mission_created" with full mission JSON
14. Connection closes
```

---

## Error Handling

```javascript
class ResilientClient {
  async connectWithRetry(maxRetries = 3) {
    for (let i = 0; i < maxRetries; i++) {
      try {
        await this.connect();
        return;
      } catch (error) {
        if (i === maxRetries - 1) throw error;
        await this.delay(2000 * Math.pow(2, i)); // Exponential backoff
      }
    }
  }

  async connect() {
    const res = await fetch('http://localhost:8000/api/v1/sessions', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${this.token}` }
    });

    if (!res.ok) throw new Error(`Session creation failed: ${res.status}`);
    
    const { session_id } = await res.json();

    return new Promise((resolve, reject) => {
      const ws = new WebSocket(
        `ws://localhost:8000/api/v1/mission-commander/ws?session_id=${session_id}&token=${this.token}`
      );

      ws.onopen = () => resolve(ws);
      ws.onerror = reject;
      setTimeout(() => reject(new Error('Timeout')), 10000);
    });
  }

  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}
```

---

## Common Issues

### Connection closes immediately
**Cause:** Server error during agent initialization  
**Fix:** Check server logs for errors, verify environment variables (API keys)

### No agent response
**Cause:** Forgot to send first message after `connected`  
**Fix:** Always send a `user_message` immediately after receiving `connected`

### "Session is inactive" error
**Cause:** Session already used or expired  
**Fix:** Create a new session for each conversation

### Mission not created
**Cause:** Incomplete conversation or confirmation not provided  
**Fix:** Ensure you answer all agent questions and confirm the learning plan

---

## Testing with curl & wscat

```bash
# 1. Create session
curl -X POST http://localhost:8000/api/v1/sessions \
  -H "Authorization: Bearer test-token"
# Returns: {"session_id": "abc123", "user_id": "user456"}

# 2. Connect WebSocket (install: npm i -g wscat)
wscat -c "ws://localhost:8000/api/v1/mission-commander/ws?session_id=abc123&token=test-token"

# 3. Send messages
{"type": "user_message", "message": "I want to learn Python"}
{"type": "user_message", "message": "For data analysis"}
{"type": "ping"}
```

---

## Production Checklist

- [ ] Use `wss://` instead of `ws://` (secure WebSocket)
- [ ] Implement connection retry with exponential backoff
- [ ] Add heartbeat ping every 30 seconds
- [ ] Handle token refresh for long conversations
- [ ] Add loading states for better UX
- [ ] Display agent handover messages as progress indicators
- [ ] Implement conversation export feature
- [ ] Add analytics tracking for conversation metrics
- [ ] Test on mobile devices and slow networks
- [ ] Set up error monitoring (Sentry, etc.)

---

## Environment URLs

```javascript
const config = {
  development: {
    api: 'http://localhost:8000',
    ws: 'ws://localhost:8000'
  },
  production: {
    api: 'https://api.yourdomain.com',
    ws: 'wss://api.yourdomain.com'
  }
};

const env = process.env.NODE_ENV || 'development';
const { api, ws } = config[env];

// Create session
const session = await fetch(`${api}/api/v1/sessions`, ...);

// Connect WebSocket
const websocket = new WebSocket(
  `${ws}/api/v1/mission-commander/ws?session_id=${sessionId}&token=${token}`
);
```

---

## Support

- **Health Check:** `GET http://localhost:8000/health`
- **Server Logs:** Check for `[ERROR]` lines during connection issues
- **Test Script:** Use backend's `test_websocket.py` for automated testing
- **Common Issues:** 90% of problems are invalid/expired tokens or missing first message

**Need help?** Check server logs, verify authentication tokens, and ensure you're sending the first `user_message` after connecting.