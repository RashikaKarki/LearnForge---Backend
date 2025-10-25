# Session Cookie Authentication Guide

## Overview

The application now uses **Firebase Session Cookies** instead of ID tokens for authentication. This provides:

- ✅ **Longer sessions** (5 days instead of 1 hour)
- ✅ **Better security** (httpOnly cookies prevent XSS attacks)
- ✅ **Automatic CSRF protection** (SameSite cookies)
- ✅ **Easier client implementation** (browser handles cookies automatically)

## Architecture Changes

### Before (ID Tokens)
```
Client → Authorization: Bearer <token> → Server
        (1 hour expiration, sent in header)
```

### After (Session Cookies)
```
Client → Cookie: session=<cookie> → Server
        (5 day expiration, automatic)
```

## Authentication Flow

### 1. Initial Sign-In

```javascript
// Client-side (React/Vue/etc.)
import { signInWithEmailAndPassword } from 'firebase/auth';

// Sign in with Firebase
const userCredential = await signInWithEmailAndPassword(auth, email, password);
const idToken = await userCredential.user.getIdToken();

// Exchange ID token for session cookie
const response = await fetch('http://your-api.com/api/v1/auth/create-session', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  credentials: 'include',  // IMPORTANT: Required for cookies
  body: JSON.stringify({ id_token: idToken })
});

// Session cookie is now automatically stored by browser
// All future requests will include it automatically
```

### 2. Making Authenticated Requests

```javascript
// All subsequent API calls automatically include the session cookie
const response = await fetch('http://your-api.com/api/v1/user/profile', {
  credentials: 'include'  // IMPORTANT: Include cookies
});
```

### 3. Logout

```javascript
// Clear session on server and browser
const response = await fetch('http://your-api.com/api/v1/auth/logout', {
  method: 'POST',
  credentials: 'include'
});
```

### 4. Check Session Status

```javascript
// Check if user is still authenticated
const response = await fetch('http://your-api.com/api/v1/auth/session-status', {
  credentials: 'include'
});

if (response.ok) {
  const data = await response.json();
  console.log('User ID:', data.uid);
} else {
  // Redirect to login
}
```

### 5. Refresh Session (Optional)

```javascript
// Extend session before it expires
const response = await fetch('http://your-api.com/api/v1/auth/refresh-session', {
  method: 'POST',
  credentials: 'include'
});
```

## API Endpoints

### POST `/api/v1/auth/create-session`

Exchange a Firebase ID token for a session cookie.

**Request:**
```json
{
  "id_token": "eyJhbGciOiJSUzI1NiIs..."
}
```

**Response:**
```json
{
  "message": "Session created successfully",
  "uid": "user123"
}
```

**Cookie Set:**
```
Set-Cookie: session=<encrypted_session_cookie>; 
            HttpOnly; 
            Secure; 
            SameSite=Lax; 
            Max-Age=432000; 
            Path=/
```

---

### POST `/api/v1/auth/logout`

Logout and clear session cookie.

**Response:**
```json
{
  "message": "Logged out successfully",
  "uid": null
}
```

**Cookie Cleared:**
```
Set-Cookie: session=; Max-Age=0; Path=/
```

---

### GET `/api/v1/auth/session-status`

Check if session is valid.

**Response (Success):**
```json
{
  "message": "Session is valid",
  "uid": "user123"
}
```

**Response (Failure):** `401 Unauthorized`

---

### POST `/api/v1/auth/refresh-session`

Extend the current session.

**Response:**
```json
{
  "message": "Session refreshed successfully",
  "uid": "user123"
}
```

## Configuration

### Backend Configuration

**Environment Variables** (`.env` or Cloud Run):
```bash
# CORS origins that can access the API
ALLOW_ORIGINS=http://localhost:3000,https://your-frontend.com

# Firebase credentials
GOOGLE_APPLICATION_CREDENTIALS=firebase_key.json

# Google API Key (for AI features)
GOOGLE_API_KEY=your_api_key_here
```

### Frontend Configuration

**Important:** Always include `credentials: 'include'` in fetch requests:

```javascript
// axios
axios.defaults.withCredentials = true;

// fetch
fetch(url, { credentials: 'include' });
```

## Security Considerations

### Cookie Settings

| Setting | Value | Purpose |
|---------|-------|---------|
| `httponly=True` | ✅ Enabled | Prevents JavaScript access (XSS protection) |
| `secure=True` | ✅ Enabled | Only sent over HTTPS (production) |
| `samesite="lax"` | ✅ Enabled | CSRF protection |
| `max_age=432000` | 5 days | Session duration |
| `path="/"` | All routes | Cookie scope |

### HTTPS Requirement

⚠️ **Important:** In production, `secure=True` requires HTTPS. For local development:

1. **Option 1:** Set `secure=False` in development
2. **Option 2:** Use a local HTTPS proxy (mkcert, ngrok, etc.)

To modify for development, update `/app/api/v1/routes/auth.py`:

```python
# For development only
SECURE_COOKIE = False  # Set to True in production

response.set_cookie(
    ...
    secure=SECURE_COOKIE,
    ...
)
```

### Recent Sign-In Check

The `create-session` endpoint requires that the user signed in within the last 5 minutes. This prevents old ID tokens from being used to create long-lived sessions.

## Error Handling

### Common Errors

| Error | Code | Cause | Solution |
|-------|------|-------|----------|
| `SESSION_MISSING` | 401 | No session cookie | Redirect to login |
| `SESSION_EXPIRED` | 401 | Cookie older than 5 days | Redirect to login |
| `SESSION_REVOKED` | 401 | User logged out | Redirect to login |
| `SESSION_INVALID` | 401 | Corrupted cookie | Clear cookies, redirect to login |

### Client-Side Error Handling

```javascript
async function makeAuthenticatedRequest(url) {
  try {
    const response = await fetch(url, { credentials: 'include' });
    
    if (response.status === 401) {
      // Session invalid - redirect to login
      window.location.href = '/login';
      return;
    }
    
    return await response.json();
  } catch (error) {
    console.error('Request failed:', error);
  }
}
```

## Migration from ID Tokens

If migrating from the old ID token system:

### 1. Update Client Code

**Before:**
```javascript
const response = await fetch(url, {
  headers: {
    'Authorization': `Bearer ${idToken}`
  }
});
```

**After:**
```javascript
const response = await fetch(url, {
  credentials: 'include'  // Cookies sent automatically
});
```

### 2. Remove Token Storage

```javascript
// Remove these - no longer needed
localStorage.removeItem('firebase_token');
sessionStorage.removeItem('firebase_token');
```

### 3. Update Sign-In Flow

Add the session creation step after Firebase sign-in:

```javascript
async function signIn(email, password) {
  // Step 1: Sign in with Firebase
  const userCredential = await signInWithEmailAndPassword(auth, email, password);
  const idToken = await userCredential.user.getIdToken();
  
  // Step 2: Create session cookie (NEW)
  await fetch('/api/v1/auth/create-session', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ id_token: idToken })
  });
  
  // Step 3: Redirect to app
  window.location.href = '/dashboard';
}
```

## Testing

### Test Session Creation

```bash
# 1. Get an ID token from Firebase (use your client app or Firebase console)

# 2. Create session
curl -X POST http://localhost:8080/api/v1/auth/create-session \
  -H "Content-Type: application/json" \
  -d '{"id_token": "YOUR_ID_TOKEN"}' \
  -c cookies.txt

# 3. Use session for authenticated request
curl http://localhost:8080/api/v1/user/profile \
  -b cookies.txt

# 4. Logout
curl -X POST http://localhost:8080/api/v1/auth/logout \
  -b cookies.txt
```

## Excluded Paths

These paths don't require authentication:

- `/api/health` - Health check
- `/docs` - API documentation
- `/openapi.json` - OpenAPI spec
- `/redoc` - Alternative API docs
- `/api/v1/auth/create-session` - Session creation
- `/api/v1/auth/logout` - Logout
- `/api/v1/auth/session-status` - Session check

## Troubleshooting

### Cookies Not Being Set

**Problem:** Session cookie not appearing in browser

**Solutions:**
1. Ensure `credentials: 'include'` in fetch requests
2. Check CORS `allow_credentials=True` is set
3. Verify frontend and backend are on same domain or proper CORS origins
4. Check HTTPS in production (secure=True requires HTTPS)

### 401 Unauthorized on Every Request

**Problem:** Session cookie not being sent

**Solutions:**
1. Check `credentials: 'include'` in all fetch requests
2. Verify cookie domain matches your frontend domain
3. Check SameSite settings (use 'lax' or 'none' for cross-domain)

### CORS Errors

**Problem:** `Access-Control-Allow-Origin` errors

**Solutions:**
1. Add your frontend URL to `ALLOW_ORIGINS` environment variable
2. Ensure `allow_credentials=True` in CORS middleware
3. Don't use `*` for allowed origins when credentials are enabled

## Production Checklist

- [ ] Set `ALLOW_ORIGINS` to your production frontend URL(s)
- [ ] Ensure `secure=True` for cookies (HTTPS only)
- [ ] Configure proper session duration (default: 5 days)
- [ ] Set up Firebase Admin SDK credentials in Cloud Run secrets
- [ ] Test logout functionality revokes refresh tokens
- [ ] Monitor failed authentication attempts
- [ ] Set up session refresh before expiration (if needed)

## References

- [Firebase Session Cookies](https://firebase.google.com/docs/auth/admin/manage-cookies)
- [FastAPI Cookies](https://fastapi.tiangolo.com/advanced/response-cookies/)
- [CORS with Credentials](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS#requests_with_credentials)
