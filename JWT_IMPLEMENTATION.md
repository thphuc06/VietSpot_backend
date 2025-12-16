# JWT Authentication Implementation Summary

## Overview

This implementation uses **Supabase's modern JWKS (JSON Web Key Set) approach** for JWT verification:

- **Algorithm:** RS256 (asymmetric cryptography)
- **Public Keys:** Automatically fetched from `{SUPABASE_URL}/auth/v1/.well-known/jwks.json`
- **No Secrets Required:** Uses public key verification instead of shared secrets
- **Automatic Key Rotation:** Supabase handles key rotation transparently
- **Security:** More secure than HS256 as the verification key is public and signing key is private

### Why JWKS/RS256 over HS256?

| Feature | RS256 (JWKS) ✅ | HS256 (Shared Secret) |
|---------|----------------|----------------------|
| Security | High - private/public key pair | Medium - shared secret |
| Key Distribution | Public key can be shared safely | Secret must be kept secure |
| Key Rotation | Automatic via JWKS | Manual configuration required |
| Configuration | None - uses public endpoint | Requires secret in environment |
| Use Case | Modern auth systems | Legacy/simple systems |

## Changes Made

### 1. Configuration Updates

#### [app/core/config.py](app/core/config.py)
- Uses existing `SUPABASE_URL` for JWKS endpoint construction
- No JWT secret needed - uses public key cryptography (RS256)

#### [.env](.env)
- No additional configuration required
- JWT verification uses public keys from `{SUPABASE_URL}/auth/v1/.well-known/jwks.json`

#### [requirements.txt](requirements.txt)
- Added `PyJWT[crypto]>=2.8.0` for JWT token verification with RS256 support

### 2. Authentication Dependencies

#### [app/api/deps.py](app/api/deps.py)
Completely rewrote authentication system:

**Removed:**
- `get_user_id_from_header()` - insecure header-based auth
- `get_optional_user_id()` - header-based optional auth

**Added:**
- `jwks_client` - PyJWKClient for fetching and caching public keys
- `verify_jwt_token(token)` - Verifies Supabase JWT tokens using RS256
- `get_current_user(credentials)` - Extracts authenticated user from JWT
- `get_current_user_id(user)` - Gets user ID from verified JWT
- `get_optional_current_user(authorization)` - Optional JWT authentication
- `get_optional_user_id(user)` - Optional user ID extraction

**Features:**
- Full JWT signature verification using **RS256 algorithm** (asymmetric cryptography)
- Automatic public key fetching from JWKS endpoint
- Public key caching for performance
- Audience validation ("authenticated")
- Proper error handling with 401 responses
- Support for optional authentication

### 3. Endpoint Updates

#### [app/api/endpoints/places.py](app/api/endpoints/places.py)

**Public Endpoints (No Auth Required):**
- `GET /places` - List places
- `GET /places/nearby` - Nearby places
- `GET /places/categories` - List categories
- `GET /places/{place_id}` - Place details

**Protected Endpoints (JWT Required):**
- `POST /places` - Create place
- `PUT /places/{place_id}` - Update place
- `DELETE /places/{place_id}` - Delete place

#### [app/api/endpoints/comments.py](app/api/endpoints/comments.py)

**Public Endpoints:**
- `GET /places/{place_id}/comments` - List comments

**Protected Endpoints (JWT Required):**
- `POST /comments` - Create comment
- `PUT /comments/{comment_id}` - Update comment
- `DELETE /comments/{comment_id}` - Delete comment
- `POST /comments/{comment_id}/images` - Add images
- `DELETE /comments/{comment_id}/images/{image_id}` - Delete image

**Changes:**
- Replaced all `Depends(get_user_id_from_header)` with `Depends(get_current_user_id)`
- Updated docstrings to reflect JWT authentication
- Removed X-User-ID header references

#### [app/api/endpoints/images.py](app/api/endpoints/images.py)

**Public Endpoints:**
- `GET /places/{place_id}/images` - Get place images
- `GET /comments/{comment_id}/images` - Get comment images

**Protected Endpoints (JWT Required):**
- `POST /upload` - Upload images

**Changes:**
- Replaced `Depends(get_user_id_from_header)` with `Depends(get_current_user_id)`
- Updated docstrings

#### [app/api/endpoints/users.py](app/api/endpoints/users.py)

**All endpoints remain public** (viewing user profiles):
- `GET /users/{user_id}/comments` - User's comments
- `GET /users/{user_id}/commented-places` - User's commented places

**Changes:**
- Added import for `get_current_user_id` (for future use if needed)
- No authentication required for viewing public user data

#### [app/api/endpoints/chat.py](app/api/endpoints/chat.py)

**Optional Authentication:**
- `POST /chat` - Chat with AI (optional user context)
- `POST /chat/itinerary/save` - Save itinerary (optional user tracking)

**Public Endpoints:**
- `GET /chat/config` - Configuration
- `GET /chat/itinerary/list/{session_id}` - List itineraries

**Changes:**
- Added `Depends(get_optional_user_id)` to endpoints that can benefit from user context
- Authentication is optional, not required

### 4. Documentation

#### [docs/JWT_AUTHENTICATION.md](docs/JWT_AUTHENTICATION.md)
Created comprehensive documentation covering:
- Setup instructions
- Authentication flow
- Endpoint protection levels
- Code examples (cURL, Python, JavaScript)
- Error handling
- Security best practices
- Migration guide from X-User-ID
- Troubleshooting

## Security Improvements

### Before (Insecure)
```bash
# Anyone could impersonate any user
curl -H "X-User-ID: any-uuid" -X POST /api/comments
```

### After (Secure)
```bash
# Only users with valid Supabase JWT can access
curl -H "Authorization: Bearer <valid-jwt>" -X POST /api/comments
```

## Authentication Flow

1. **Client authenticates with Supabase:**
   ```javascript
   const { data } = await supabase.auth.signInWithPassword({ email, password })
   const token = data.session.access_token
   ```

2. **Client sends token to API:**
   ```http
   Authorization: Bearer <token>
   ```

3. **API verifies token:**
   - Validates signature using `SUPABASE_JWT_SECRET`
   - Checks expiration
   - Validates audience
   - Extracts user ID from `sub` claim

4. **API executes request with user context**

## Token Verification Details

```python
# Fetch signing key from JWKS endpoint
signing_key = jwks_client.get_signing_key_from_jwt(token)

# Verify token with RS256 public key
jwt.decode(
    token,
    signing_key.key,
    algorithms=["RS256"],
    audience="authenticated"
)
```

**Token payload example:**
```json
{
  "sub": "user-uuid",
  "email": "user@example.com",
  "aud": "authenticated",
  "role": "authenticated",
  "iat": 1734316800,
  "exp": 1734320400
}
```

## Endpoints Summary

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/places` | GET | Public | List places |
| `/places` | POST | **Required** | Create place |
| `/places/{id}` | GET | Public | Get place details |
| `/places/{id}` | PUT | **Required** | Update place |
| `/places/{id}` | DELETE | **Required** | Delete place |
| `/comments` | POST | **Required** | Create comment |
| `/comments/{id}` | PUT | **Required** | Update comment |
| `/comments/{id}` | DELETE | **Required** | Delete comment |
| `/upload` | POST | **Required** | Upload images |
| `/chat` | POST | Optional | AI chat |
| `/users/{id}/comments` | GET | Public | User comments |

## Testing

### Get JWT Token
```javascript
// Using Supabase client
const { data } = await supabase.auth.signInWithPassword({
  email: 'test@example.com',
  password: 'password'
})
const token = data.session.access_token
```

### Test Protected Endpoint
```bash
curl -X POST "http://localhost:8000/api/comments" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"place_id":"uuid","rating":5,"text":"Great!"}'
```

## Migration Checklist

- [x] Add PyJWT[crypto] dependency
- [x] Configure JWKS client with RS256
- [x] Create JWT verification functions using public keys
- [x] Update all protected endpoints
- [x] Update documentation
- [x] Remove X-User-ID header authentication
- [x] Add error handling
- [x] Create migration guide
- [x] No secrets configuration needed

## Next Steps

1. **No Configuration Needed:**
   - JWT verification automatically uses public keys from Supabase
   - JWKS endpoint: `{SUPABASE_URL}/auth/v1/.well-known/jwks.json`

2. **Update Frontend:**
   - Remove X-User-ID headers
   - Add Authorization headers with JWT tokens
   - Handle 401 errors and token refresh

3. **Test Authentication:**
   - Test all protected endpoints
   - Verify ownership checks work
   - Test optional authentication endpoints

4. **Deploy:**
   - Ensure JWT secret is in production environment
   - Update API documentation
   - Notify frontend team of changes

## Breaking Changes

⚠️ **This is a breaking change for API clients:**

- All endpoints that previously used `X-User-ID` header now require `Authorization: Bearer <jwt>` header
- Clients must authenticate through Supabase Auth before accessing protected endpoints
- Invalid or missing tokens will return 401 errors

## Security Notes

- **No secrets to manage** - uses public key cryptography (RS256)
- Public keys are automatically fetched and cached from Supabase JWKS endpoint
- Tokens are signed with Supabase's private key and verified with public key
- Tokens expire after 1 hour (Supabase default)
- Always use HTTPS in production
- Implement token refresh on client side
- Consider rate limiting for authentication endpoints
- Key rotation is handled automatically by Supabase
