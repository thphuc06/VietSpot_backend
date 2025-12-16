# JWT Authentication with JWKS - Quick Start Guide

## How It Works

The VietSpot API uses **Supabase JWT authentication with JWKS (JSON Web Key Set)**:

1. Users authenticate with Supabase Auth (sign up/sign in)
2. Supabase returns a JWT token signed with its private key (RS256)
3. Client sends token in `Authorization: Bearer <token>` header
4. API automatically fetches Supabase's public key from JWKS endpoint
5. API verifies token signature using the public key
6. If valid, request proceeds with user context

## Frontend Integration

### 1. User Authentication (Supabase)

```javascript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  'https://aaezaowgeonxzpcafesa.supabase.co',
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...' // anon key
)

// Sign up
const { data, error } = await supabase.auth.signUp({
  email: 'user@example.com',
  password: 'secure-password'
})

// Sign in
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'secure-password'
})

// Get access token
const token = data.session.access_token
```

### 2. Making API Requests

```javascript
// Store token after authentication
const token = data.session.access_token

// Make authenticated request
const response = await fetch('http://localhost:8000/api/comments', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    place_id: 'uuid-here',
    rating: 5,
    text: 'Great place!'
  })
})
```

### 3. Using with Axios

```javascript
import axios from 'axios'

// Create axios instance with interceptor
const api = axios.create({
  baseURL: 'http://localhost:8000/api'
})

// Add token to all requests
api.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Use it
const response = await api.post('/comments', {
  place_id: 'uuid-here',
  rating: 5,
  text: 'Great place!'
})
```

### 4. Token Refresh

```javascript
// Supabase automatically refreshes tokens
supabase.auth.onAuthStateChange((event, session) => {
  if (event === 'TOKEN_REFRESHED') {
    const newToken = session.access_token
    // Update stored token
    localStorage.setItem('access_token', newToken)
  }
})
```

## Backend (Python) Testing

### Using requests library

```python
import requests

# Get token from Supabase (you'd normally do this via Supabase client)
token = "eyJhbGciOiJSUzI1NiIsImtpZCI6..."

# Make authenticated request
response = requests.post(
    'http://localhost:8000/api/comments',
    headers={'Authorization': f'Bearer {token}'},
    json={
        'place_id': 'uuid-here',
        'rating': 5,
        'text': 'Great place!'
    }
)
```

### Using httpx (async)

```python
import httpx

async def create_comment(token: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            'http://localhost:8000/api/comments',
            headers={'Authorization': f'Bearer {token}'},
            json={
                'place_id': 'uuid-here',
                'rating': 5,
                'text': 'Great place!'
            }
        )
        return response.json()
```

## Testing with cURL

```bash
# Set your token
TOKEN="your-jwt-token-here"

# Test protected endpoint
curl -X POST "http://localhost:8000/api/comments" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "place_id": "uuid-here",
    "rating": 5,
    "text": "Great place!",
    "author_name": "Test User"
  }'

# Test public endpoint (no auth needed)
curl "http://localhost:8000/api/places"
```

## Endpoint Authentication Requirements

### 🔓 Public Endpoints (No Auth)
- `GET /places` - List all places
- `GET /places/{id}` - Get place details
- `GET /places/nearby` - Get nearby places
- `GET /places/categories` - List categories
- `GET /places/{id}/comments` - Get place comments
- `GET /places/{id}/images` - Get place images
- `GET /users/{id}/comments` - Get user comments
- `GET /users/{id}/commented-places` - Get user's places
- `GET /chat/config` - Chat configuration
- `POST /chat` - AI chat (optional auth)

### 🔒 Protected Endpoints (Auth Required)
- `POST /places` - Create place
- `PUT /places/{id}` - Update place
- `DELETE /places/{id}` - Delete place
- `POST /comments` - Create comment
- `PUT /comments/{id}` - Update comment
- `DELETE /comments/{id}` - Delete comment
- `POST /comments/{id}/images` - Add images to comment
- `DELETE /comments/{id}/images/{image_id}` - Remove image
- `POST /upload` - Upload images

## Error Handling

### 401 Unauthorized

```json
{
  "detail": "Token has expired"
}
```

**Fix:** Refresh the token using Supabase client

```json
{
  "detail": "Invalid authentication token: ..."
}
```

**Fix:** Ensure you're using a valid JWT from Supabase Auth

### 403 Forbidden

```json
{
  "detail": "You do not have permission to access this resource"
}
```

**Fix:** User doesn't own the resource (e.g., trying to edit someone else's comment)

## Token Payload

When decoded, the JWT contains:

```json
{
  "sub": "user-uuid",           // User ID
  "email": "user@example.com",  // User email
  "aud": "authenticated",        // Audience
  "role": "authenticated",       // User role
  "iat": 1734316800,            // Issued at
  "exp": 1734320400             // Expires at
}
```

Access user info in endpoints:
```python
@router.get("/me")
async def get_current_user_info(user: dict = Depends(get_current_user)):
    return {
        "user_id": user["sub"],
        "email": user["email"],
        "role": user["role"]
    }
```

## Security Best Practices

1. **Always use HTTPS in production**
2. **Never log or expose JWT tokens**
3. **Store tokens securely** (e.g., httpOnly cookies, secure storage)
4. **Implement token refresh** before expiration
5. **Handle 401 errors** by redirecting to login
6. **Validate token on every request** (done automatically by API)

## JWKS Endpoint

The API fetches public keys from:
```
https://aaezaowgeonxzpcafesa.supabase.co/auth/v1/.well-known/jwks.json
```

You can view it in your browser - it's public and safe to share!

## No Configuration Required! 🎉

Unlike traditional JWT implementations, this approach requires:
- ❌ No JWT secret to configure
- ❌ No manual key management
- ❌ No key rotation worries
- ✅ Automatic public key fetching
- ✅ Automatic key caching
- ✅ Automatic key rotation support

The API automatically fetches and validates tokens using Supabase's public JWKS endpoint!
