# WebSocket Authentication Guide

## Overview

The Mission Commander WebSocket endpoint supports **three authentication methods** to accommodate different client types.

## Authentication Methods

### 1. Query Parameter (Current Default)
**Use case:** Simple integration, testing  
**Security:** ⚠️ Lower (token visible in URL/logs)

```javascript
// Browser client
const ws = new WebSocket(
  `ws://localhost:8000/api/v1/mission-commander/ws?session_id=${sessionId}&token=${token}`
);
```

```python
# Python client
import websockets

async with websockets.connect(
    f"ws://localhost:8000/api/v1/mission-commander/ws?session_id={session_id}&token={token}"
) as ws:
    # Use websocket
```

### 2. Cookie (Recommended for Browsers)
**Use case:** Web applications  
**Security:** ✅ Higher (HttpOnly cookies, not visible in URL)

```javascript
// Set cookie before connecting (e.g., after login)
document.cookie = `token=${authToken}; path=/; secure; samesite=strict`;

// Connect without token in URL
const ws = new WebSocket(
  `ws://localhost:8000/api/v1/mission-commander/ws?session_id=${sessionId}`
);
```

**Backend automatically reads cookie:**
- Cookie name: `token`
- Automatically sent with WebSocket upgrade request
- No code changes needed on client after cookie is set

### 3. Authorization Header (Server-to-Server Only)
**Use case:** Backend services, CLI tools  
**Security:** ✅ Highest (standard OAuth2/JWT pattern)

⚠️ **Note:** Browsers cannot set custom headers on WebSocket connections. This only works for non-browser clients.

```python
# Python client with custom headers
import websockets

async with websockets.connect(
    f"ws://localhost:8000/api/v1/mission-commander/ws?session_id={session_id}",
    extra_headers={"Authorization": f"Bearer {token}"}
) as ws:
    # Use websocket
```

```javascript
// Node.js client
const WebSocket = require('ws');

const ws = new WebSocket(
  `ws://localhost:8000/api/v1/mission-commander/ws?session_id=${sessionId}`,
  {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  }
);
```

## Priority Order

The server checks authentication sources in this order:

1. **Query parameter** `?token=xxx` (checked first for backward compatibility)
2. **Cookie** `token=xxx` (fallback if query param missing)
3. **Authorization header** `Bearer xxx` (fallback if both above missing)

## Security Recommendations

### For Production Web Apps (Frontend)
✅ **Use Cookies**
```javascript
// After successful login, set HttpOnly cookie on server
// Response from /api/v1/auth/login:
Set-Cookie: token=<jwt>; HttpOnly; Secure; SameSite=Strict; Path=/

// Then connect to WebSocket (cookie sent automatically)
const ws = new WebSocket(`wss://app.com/api/v1/mission-commander/ws?session_id=${id}`);
```

### For Backend Services
✅ **Use Authorization Header**
```python
headers = {"Authorization": f"Bearer {jwt_token}"}
async with websockets.connect(url, extra_headers=headers) as ws:
    pass
```

### For Testing/Development Only
⚠️ **Query Parameter** (acceptable for local development)
```bash
# Easy to test with tools like wscat
wscat -c "ws://localhost:8000/api/v1/mission-commander/ws?session_id=123&token=test"
```

## Migration Guide

### From Query Param to Cookie

**Before:**
```javascript
const token = localStorage.getItem('authToken');
const ws = new WebSocket(
  `ws://localhost:8000/api/v1/mission-commander/ws?session_id=${id}&token=${token}`
);
```

**After:**
```javascript
// 1. Modify your login endpoint to set HttpOnly cookie
// (Server-side change - see example below)

// 2. Remove token from WebSocket URL
const ws = new WebSocket(
  `ws://localhost:8000/api/v1/mission-commander/ws?session_id=${id}`
);
// Cookie is sent automatically!
```

**Server-side login endpoint example:**
```python
from fastapi import Response

@router.post("/auth/login")
async def login(credentials: LoginCredentials, response: Response):
    # Validate credentials and generate token
    token = create_jwt_token(user_id)
    
    # Set HttpOnly cookie
    response.set_cookie(
        key="token",
        value=token,
        httponly=True,  # Prevents JavaScript access
        secure=True,    # HTTPS only
        samesite="strict",  # CSRF protection
        max_age=3600 * 24 * 7  # 7 days
    )
    
    return {"message": "Login successful"}
```

## Testing Different Methods

```python
# Test with pytest
import pytest
from unittest.mock import MagicMock

@pytest.fixture
def mock_websocket():
    ws = MagicMock()
    ws.query_params = {}
    ws.cookies = {}
    ws.headers = {}
    return ws

async def test_auth_via_query_param(mock_websocket):
    mock_websocket.query_params = {"token": "test_token"}
    # Test validates successfully

async def test_auth_via_cookie(mock_websocket):
    mock_websocket.cookies = {"token": "test_token"}
    # Test validates successfully

async def test_auth_via_header(mock_websocket):
    mock_websocket.headers = {"authorization": "Bearer test_token"}
    # Test validates successfully
```

## Common Issues

### Issue: Cookie not being sent
**Solution:** Ensure cookie domain and path match WebSocket URL
```javascript
// If WebSocket is at wss://api.example.com/ws
// Cookie must be set with:
document.cookie = "token=xxx; domain=.example.com; path=/";
```

### Issue: CORS blocking cookie
**Solution:** Configure CORS to allow credentials
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.example.com"],
    allow_credentials=True,  # Required for cookies
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Issue: Authorization header not working in browser
**Solution:** Use cookies instead. Browsers cannot set WebSocket headers from JavaScript.

## Summary

| Method | Security | Browser Support | Use Case |
|--------|----------|-----------------|----------|
| Query Param | ⚠️ Low | ✅ Yes | Development, Testing |
| Cookie | ✅ High | ✅ Yes | **Production Web Apps** |
| Header | ✅ Highest | ❌ No | **Backend Services** |

**Recommendation:** Use cookies for browser clients, headers for server-to-server communication.
