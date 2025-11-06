# Mission Ally WebSocket API

A conversational AI agent that guides users through learning missions via WebSocket. This endpoint allows real-time interaction with the Mission Ally agent to complete learning checkpoints.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Connection & Authentication](#connection--authentication)
- [Endpoint Details](#endpoint-details)
- [Message Types](#message-types)
  - [Client → Server Messages](#client--server-messages)
  - [Server → Client Messages](#server--client-messages)
- [Complete Examples](#complete-examples)
- [Error Handling](#error-handling)
- [Best Practices](#best-practices)

---

## Quick Start

### 1. Connect to WebSocket

```javascript
// Get your Firebase session token (from your auth system)
const token = await getFirebaseSessionToken(); // Your implementation
const missionId = "p3BpROIATqthZT3ckEzd"; // The mission ID to learn

// Connect to WebSocket
const ws = new WebSocket(
  `ws://localhost:8080/api/v1/mission-ally/ws?mission_id=${missionId}&token=${token}`
);

// Handle connection
ws.onopen = () => {
  console.log("Connected to Mission Ally");
};

// Handle messages
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  handleMessage(message);
};

// Send your first message
ws.onopen = () => {
  ws.send(JSON.stringify({
    type: "user_message",
    message: "Hello, I'm ready to start learning!"
  }));
};
```

---

## Connection & Authentication

### Endpoint URL

```
ws://{host}:{port}/api/v1/mission-ally/ws
```

### Required Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `mission_id` | string | ✅ Yes | The ID of the mission the user is enrolled in |

### Authentication

The WebSocket endpoint supports **three authentication methods** (checked in this order):

1. **Query Parameter** (Development/Testing)
   ```javascript
   const ws = new WebSocket(
     `ws://localhost:8080/api/v1/mission-ally/ws?mission_id=${missionId}&token=${token}`
   );
   ```

2. **Cookie** (Recommended for Production)
   ```javascript
   // Set cookie after login (server-side)
   // Cookie name: "token"
   
   // Connect without token in URL
   const ws = new WebSocket(
     `ws://localhost:8080/api/v1/mission-ally/ws?mission_id=${missionId}`
   );
   ```

3. **Authorization Header** (Server-to-Server Only)
   ```python
   # Python/Node.js only - browsers cannot set WebSocket headers
   headers = {"Authorization": f"Bearer {token}"}
   ```

### Token Format

The token must be a **Firebase session cookie token** (JWT). The token is verified using `firebase_admin.auth.verify_session_cookie()`.

**Example:**
```javascript
// Get token from Firebase Auth
import { getAuth } from "firebase/auth";

const auth = getAuth();
const user = auth.currentUser;
const token = await user.getIdToken(); // This is a Firebase ID token

// Convert to session cookie (typically done server-side)
// For production, use your backend to exchange ID token for session cookie
```

---

## Endpoint Details

### WebSocket URL Structure

```
ws://{host}:{port}/api/v1/mission-ally/ws?mission_id={mission_id}&token={firebase_token}
```

**Example:**
```
ws://localhost:8080/api/v1/mission-ally/ws?mission_id=p3BpROIATqthZT3ckEzd&token=eyJhbGc...
```

### Connection Flow

1. **Client connects** → WebSocket handshake
2. **Server authenticates** → Validates Firebase token
3. **Server initializes session** → Fetches enrollment, mission, and session data
4. **Server sends `connected`** → Connection established
5. **Server sends `historical_messages`** (if any) → Previous conversation history
6. **Client sends `user_message`** → Starts conversation
7. **Server processes** → Sends `agent_processing_start`, then `agent_message`, then `agent_processing_end`
8. **Conversation continues** → Repeat steps 6-7

### Connection Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| `1000` | Normal Closure | Connection closed normally |
| `1008` | Policy Violation | Authentication failed or invalid mission/enrollment |
| `1011` | Internal Error | Server error during processing |

---

## Message Types

### Client → Server Messages

#### 1. User Message

Send a message to the agent to continue the conversation.

**Format:**
```json
{
  "type": "user_message",
  "message": "string"
}
```

**Fields:**
- `type` (string, required): Must be `"user_message"`
- `message` (string, required): The user's message (min length: 1)

**Example:**
```json
{
  "type": "user_message",
  "message": "I've completed the first checkpoint!"
}
```

**JavaScript:**
```javascript
ws.send(JSON.stringify({
  type: "user_message",
  message: "I've completed the first checkpoint!"
}));
```

---

#### 2. Ping (Keepalive)

Keep the connection alive. Server responds with `pong`.

**Format:**
```json
{
  "type": "ping"
}
```

**Example:**
```json
{
  "type": "ping"
}
```

**JavaScript:**
```javascript
// Send ping every 30 seconds to keep connection alive
const pingInterval = setInterval(() => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: "ping" }));
  }
}, 30000);
```

---

### Server → Client Messages

#### 1. Connected

Sent immediately after successful WebSocket connection and authentication.

**Format:**
```json
{
  "type": "connected",
  "message": "string"
}
```

**Fields:**
- `type` (string): `"connected"`
- `message` (string): Welcome message

**Example:**
```json
{
  "type": "connected",
  "message": "Connected to Lumina. Ready to start learning!"
}
```

**JavaScript:**
```javascript
ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  
  if (msg.type === "connected") {
    console.log(msg.message); // "Connected to Lumina. Ready to start learning!"
    // Now you can send your first user_message
  }
};
```

---

#### 2. Historical Messages

Sent after `connected` if there are previous messages in this session. Contains the conversation history.

**Format:**
```json
{
  "type": "historical_messages",
  "messages": [
    {
      "type": "user_message" | "agent_message",
      "message": "string"
    }
  ]
}
```

**Fields:**
- `type` (string): `"historical_messages"`
- `messages` (array): List of previous messages

**Message Object Format:**
- `type` (string): `"user_message"` or `"agent_message"`
- `message` (string): The message text

**Example:**
```json
{
  "type": "historical_messages",
  "messages": [
    {
      "type": "user_message",
      "message": "Hello!"
    },
    {
      "type": "agent_message",
      "message": "Hi! Ready to start learning?"
    }
  ]
}
```

**JavaScript:**
```javascript
if (msg.type === "historical_messages") {
  // Restore previous conversation in UI
  msg.messages.forEach(historicalMsg => {
    if (historicalMsg.type === "user_message") {
      displayUserMessage(historicalMsg.message);
    } else if (historicalMsg.type === "agent_message") {
      displayAgentMessage(historicalMsg.message);
    }
  });
}
```

---

#### 3. Agent Processing Start

Sent when the agent starts processing a user message. Use this to show a typing indicator.

**Format:**
```json
{
  "type": "agent_processing_start"
}
```

**Fields:**
- `type` (string): `"agent_processing_start"`

**Example:**
```json
{
  "type": "agent_processing_start"
}
```

**JavaScript:**
```javascript
if (msg.type === "agent_processing_start") {
  showTypingIndicator(); // Show "Agent is typing..." in UI
}
```

---

#### 4. Agent Message

The agent's response to the user. May be sent multiple times during processing (streaming).

**Format:**
```json
{
  "type": "agent_message",
  "message": "string"
}
```

**Fields:**
- `type` (string): `"agent_message"`
- `message` (string): The agent's message text

**Example:**
```json
{
  "type": "agent_message",
  "message": "Great job! You've completed the first checkpoint. Let's move on to the next one."
}
```

**JavaScript:**
```javascript
if (msg.type === "agent_message") {
  displayAgentMessage(msg.message);
  // Keep typing indicator visible until agent_processing_end
}
```

---

#### 5. Agent Processing End

Sent when the agent finishes processing a user message. Use this to hide the typing indicator.

**Format:**
```json
{
  "type": "agent_processing_end"
}
```

**Fields:**
- `type` (string): `"agent_processing_end"`

**Example:**
```json
{
  "type": "agent_processing_end"
}
```

**JavaScript:**
```javascript
if (msg.type === "agent_processing_end") {
  hideTypingIndicator(); // Hide "Agent is typing..." in UI
}
```

**Note:** Always wait for `agent_processing_end` before hiding the typing indicator, even if you've received `agent_message` (messages may stream in chunks).

---

#### 6. Agent Handover

Sent when the agent transfers control to another internal agent. This is informational only.

**Format:**
```json
{
  "type": "agent_handover",
  "agent": "string",
  "message": "string"
}
```

**Fields:**
- `type` (string): `"agent_handover"`
- `agent` (string): Name of the agent being transferred to
- `message` (string): Handover message

**Example:**
```json
{
  "type": "agent_handover",
  "agent": "mission_sensei",
  "message": "Handing over to mission_sensei..."
}
```

**JavaScript:**
```javascript
if (msg.type === "agent_handover") {
  console.log(`Agent handover to ${msg.agent}: ${msg.message}`);
  // Optionally show in UI: "Switching to ${msg.agent}..."
}
```

---

#### 7. Checkpoint Update

Sent when the user completes a checkpoint. Updates progress percentage.

**Format:**
```json
{
  "type": "checkpoint_update",
  "completed_checkpoints": ["string"],
  "progress": 0.0-100.0
}
```

**Fields:**
- `type` (string): `"checkpoint_update"`
- `completed_checkpoints` (array of strings): List of completed checkpoint IDs
- `progress` (float): Progress percentage (0.0 to 100.0)

**Example:**
```json
{
  "type": "checkpoint_update",
  "completed_checkpoints": ["checkpoint_1", "checkpoint_2"],
  "progress": 66.67
}
```

**JavaScript:**
```javascript
if (msg.type === "checkpoint_update") {
  updateProgressBar(msg.progress);
  console.log(`Completed checkpoints: ${msg.completed_checkpoints.join(", ")}`);
  console.log(`Progress: ${msg.progress.toFixed(1)}%`);
}
```

---

#### 8. Session Closed

Sent when the mission is completed. The WebSocket connection will be closed by the server shortly after.

**Format:**
```json
{
  "type": "session_closed",
  "message": "string"
}
```

**Fields:**
- `type` (string): `"session_closed"`
- `message` (string): Completion message

**Example:**
```json
{
  "type": "session_closed",
  "message": "Congratulations! You've completed the mission!"
}
```

**JavaScript:**
```javascript
if (msg.type === "session_closed") {
  showCompletionMessage(msg.message);
  // Connection will close automatically by server
  ws.onclose = () => {
    console.log("Session completed and connection closed");
  };
}
```

---

#### 9. Pong

Response to a `ping` message. Used for connection keepalive.

**Format:**
```json
{
  "type": "pong"
}
```

**Fields:**
- `type` (string): `"pong"`

**Example:**
```json
{
  "type": "pong"
}
```

**JavaScript:**
```javascript
if (msg.type === "pong") {
  // Connection is alive, no action needed
}
```

---

#### 10. Error

Sent when an error occurs during processing.

**Format:**
```json
{
  "type": "error",
  "message": "string"
}
```

**Fields:**
- `type` (string): `"error"`
- `message` (string): Error message (user-friendly, sanitized)

**Example:**
```json
{
  "type": "error",
  "message": "Invalid message format: missing required field 'message'"
}
```

**JavaScript:**
```javascript
if (msg.type === "error") {
  showError(msg.message);
  // Optionally close connection
  ws.close();
}
```

---

## Complete Examples

### Example 1: Basic Chat Flow

```javascript
class MissionAllyClient {
  constructor(missionId, token) {
    this.missionId = missionId;
    this.token = token;
    this.ws = null;
  }

  connect() {
    const url = `ws://localhost:8080/api/v1/mission-ally/ws?mission_id=${this.missionId}&token=${this.token}`;
    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      console.log("Connected to Mission Ally");
    };

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.handleMessage(message);
    };

    this.ws.onerror = (error) => {
      console.error("WebSocket error:", error);
    };

    this.ws.onclose = (event) => {
      console.log("Connection closed", event.code, event.reason);
    };
  }

  handleMessage(msg) {
    switch (msg.type) {
      case "connected":
        console.log("Connected:", msg.message);
        break;

      case "historical_messages":
        console.log("Loading", msg.messages.length, "historical messages");
        msg.messages.forEach(m => {
          if (m.type === "user_message") {
            this.displayUserMessage(m.message);
          } else if (m.type === "agent_message") {
            this.displayAgentMessage(m.message);
          }
        });
        break;

      case "agent_processing_start":
        this.showTypingIndicator();
        break;

      case "agent_message":
        this.displayAgentMessage(msg.message);
        break;

      case "agent_processing_end":
        this.hideTypingIndicator();
        break;

      case "checkpoint_update":
        this.updateProgress(msg.progress, msg.completed_checkpoints);
        break;

      case "session_closed":
        this.showCompletion(msg.message);
        break;

      case "error":
        this.showError(msg.message);
        break;

      case "pong":
        // Connection alive
        break;

      default:
        console.warn("Unknown message type:", msg.type);
    }
  }

  sendMessage(text) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: "user_message",
        message: text
      }));
      this.displayUserMessage(text);
    }
  }

  displayUserMessage(text) {
    console.log("User:", text);
    // Add to UI
  }

  displayAgentMessage(text) {
    console.log("Agent:", text);
    // Add to UI
  }

  showTypingIndicator() {
    console.log("Agent is typing...");
    // Show typing indicator in UI
  }

  hideTypingIndicator() {
    console.log("Agent finished typing");
    // Hide typing indicator in UI
  }

  updateProgress(progress, checkpoints) {
    console.log(`Progress: ${progress}%`, checkpoints);
    // Update progress bar in UI
  }

  showCompletion(message) {
    console.log("Mission completed:", message);
    // Show completion screen
  }

  showError(message) {
    console.error("Error:", message);
    // Show error in UI
  }
}

// Usage
const client = new MissionAllyClient("p3BpROIATqthZT3ckEzd", "your_token");
client.connect();

// Send a message
client.sendMessage("Hello, I'm ready to start!");
```

---

### Example 2: React Hook

```javascript
import { useState, useEffect, useRef } from 'react';

function useMissionAlly(missionId, token) {
  const [messages, setMessages] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [progress, setProgress] = useState(0);
  const wsRef = useRef(null);

  useEffect(() => {
    const url = `ws://localhost:8080/api/v1/mission-ally/ws?mission_id=${missionId}&token=${token}`;
    wsRef.current = new WebSocket(url);

    wsRef.current.onopen = () => {
      setIsConnected(true);
    };

    wsRef.current.onmessage = (event) => {
      const msg = JSON.parse(event.data);

      switch (msg.type) {
        case 'connected':
          break;

        case 'historical_messages':
          setMessages(msg.messages.map(m => ({
            role: m.type === 'user_message' ? 'user' : 'agent',
            text: m.message
          })));
          break;

        case 'agent_processing_start':
          setIsTyping(true);
          break;

        case 'agent_message':
          setMessages(prev => [...prev, { role: 'agent', text: msg.message }]);
          break;

        case 'agent_processing_end':
          setIsTyping(false);
          break;

        case 'checkpoint_update':
          setProgress(msg.progress);
          break;

        case 'session_closed':
          setIsConnected(false);
          break;

        case 'error':
          console.error('Error:', msg.message);
          break;
      }
    };

    wsRef.current.onclose = () => {
      setIsConnected(false);
    };

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [missionId, token]);

  const sendMessage = (text) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'user_message',
        message: text
      }));
      setMessages(prev => [...prev, { role: 'user', text }]);
    }
  };

  return {
    messages,
    isConnected,
    isTyping,
    progress,
    sendMessage
  };
}

// Usage in component
function MissionAllyChat({ missionId, token }) {
  const { messages, isConnected, isTyping, progress, sendMessage } = useMissionAlly(missionId, token);
  const [input, setInput] = useState('');

  return (
    <div>
      <div>Progress: {progress}%</div>
      <div>Status: {isConnected ? 'Connected' : 'Disconnected'}</div>
      
      <div className="messages">
        {messages.map((msg, i) => (
          <div key={i} className={msg.role}>
            {msg.text}
          </div>
        ))}
        {isTyping && <div>Agent is typing...</div>}
      </div>

      <input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyPress={(e) => {
          if (e.key === 'Enter' && input.trim()) {
            sendMessage(input);
            setInput('');
          }
        }}
      />
      <button onClick={() => {
        if (input.trim()) {
          sendMessage(input);
          setInput('');
        }
      }}>
        Send
      </button>
    </div>
  );
}
```

---

## Error Handling

### Connection Errors

```javascript
ws.onerror = (error) => {
  console.error("WebSocket error:", error);
  // Show error to user
};

ws.onclose = (event) => {
  if (event.code === 1008) {
    console.error("Authentication failed or invalid mission/enrollment");
  } else if (event.code === 1011) {
    console.error("Server error:", event.reason);
  } else {
    console.log("Connection closed:", event.code, event.reason);
  }
  
  // Optionally attempt to reconnect
  if (event.code !== 1000 && event.code !== 1008) {
    setTimeout(() => reconnect(), 3000);
  }
};
```

### Message Errors

```javascript
ws.onmessage = (event) => {
  try {
    const msg = JSON.parse(event.data);
    
    if (msg.type === "error") {
      // Handle server-sent error
      showError(msg.message);
    } else {
      handleMessage(msg);
    }
  } catch (e) {
    console.error("Failed to parse message:", e);
  }
};
```

### Invalid Message Format

If you send an invalid message, the server will respond with an error:

```json
{
  "type": "error",
  "message": "Invalid message format: missing required field 'message'"
}
```

---

## Best Practices

### 1. Authentication

✅ **Do:**
- Use cookies for production web apps
- Store tokens securely (never in localStorage for sensitive apps)
- Refresh tokens before they expire

❌ **Don't:**
- Expose tokens in URLs in production
- Hardcode tokens in client code
- Send tokens in plain text

### 2. Connection Management

✅ **Do:**
- Implement reconnection logic with exponential backoff
- Handle connection errors gracefully
- Send ping messages to keep connection alive (every 30 seconds)

❌ **Don't:**
- Create multiple connections for the same session
- Ignore connection close events
- Leave connections open indefinitely without pings

### 3. Message Handling

✅ **Do:**
- Always check `msg.type` before processing
- Handle all message types (even if you don't use them)
- Show typing indicator when `agent_processing_start` is received
- Hide typing indicator only when `agent_processing_end` is received

❌ **Don't:**
- Assume message order (messages may arrive out of order)
- Hide typing indicator on `agent_message` (wait for `agent_processing_end`)
- Ignore error messages

### 4. UI/UX

✅ **Do:**
- Show connection status to users
- Display progress updates
- Show typing indicator during agent processing
- Handle historical messages to restore conversation state
- Show completion screen when mission is done

❌ **Don't:**
- Block UI while waiting for agent response
- Show errors without context
- Ignore checkpoint updates

### 5. Error Recovery

✅ **Do:**
- Implement retry logic for failed messages
- Handle network interruptions gracefully
- Show user-friendly error messages
- Log errors for debugging

---

## Message Flow Diagram

```
Client                          Server
  |                               |
  |--- Connect WebSocket -------->|
  |                               | (Authenticate)
  |                               | (Initialize Session)
  |<-- connected -----------------|
  |<-- historical_messages -------|
  |                               |
  |--- user_message ------------->|
  |                               | (Process)
  |<-- agent_processing_start ----|
  |<-- agent_message -------------|
  |<-- agent_message (stream) ----|
  |<-- agent_processing_end ------|
  |                               |
  |--- user_message ------------->|
  |                               | (Checkpoint completed)
  |<-- agent_processing_start ----|
  |<-- agent_message -------------|
  |<-- checkpoint_update ---------|
  |<-- agent_processing_end ------|
  |                               |
  |--- user_message ------------->|
  |                               | (Mission completed)
  |<-- agent_processing_start ----|
  |<-- agent_message -------------|
  |<-- session_closed ------------|
  |                               | (Close connection)
```

---

## Troubleshooting

### Issue: Connection fails with code 1008

**Cause:** Authentication failed or invalid mission/enrollment

**Solutions:**
- Verify token is valid Firebase session cookie
- Check that user is enrolled in the mission
- Ensure mission_id is correct

### Issue: No messages received

**Cause:** Connection not properly established

**Solutions:**
- Check WebSocket URL format
- Verify token is included
- Check browser console for connection errors

### Issue: Typing indicator never hides

**Cause:** `agent_processing_end` not received

**Solutions:**
- Ensure you're handling `agent_processing_end` message
- Add timeout fallback (e.g., hide after 30 seconds)
- Check server logs for errors

### Issue: Historical messages not showing

**Cause:** Session is new or messages not properly formatted

**Solutions:**
- Verify session was started previously
- Check message format in `historical_messages` array
- Handle both `user_message` and `agent_message` types

---

## Summary

| Feature | Description |
|---------|-------------|
| **Endpoint** | `ws://{host}:{port}/api/v1/mission-ally/ws` |
| **Auth** | Firebase session cookie (query param, cookie, or header) |
| **Required Param** | `mission_id` (query parameter) |
| **Client Messages** | `user_message`, `ping` |
| **Server Messages** | `connected`, `historical_messages`, `agent_processing_start`, `agent_message`, `agent_processing_end`, `agent_handover`, `checkpoint_update`, `session_closed`, `pong`, `error` |
| **Typing Indicator** | Show on `agent_processing_start`, hide on `agent_processing_end` |
| **Progress Updates** | Received via `checkpoint_update` message |

---

For more information on authentication, see [WEBSOCKET_AUTHENTICATION.md](./WEBSOCKET_AUTHENTICATION.md).

