# TradeLogger Security Fix Plan

**Generated:** 2026-04-01  
**Audit By:** @security-engineer  
**Total Issues Found:** 16 (5 Critical, 4 High, 4 Medium, 3 Low)

---

## 🚨 CRITICAL SEVERITY (Fix Immediately)

### SEC-001: No Authentication/Authorization System
**Risk:** Unauthorized access to all trading data, ability to create/modify/delete trades, accounts, and favorites.

**Files Affected:** Entire application (all routes)

**Status:** ✅ COMPLETE - All 4 auth sessions implemented

**Summary:**
Complete authentication system has been implemented with:
- User model with support for both Google OAuth and Email/Password authentication
- JWT token-based authentication with HttpOnly cookies
- Route protection with @jwt_required decorator
- Frontend login page with both auth methods
- User isolation - users only see their own data
- Automatic token refresh (every 13 minutes)

**All Sessions Complete!** ✅

**Session 1: auth-database-session** ✅
- Added Alembic for database migrations
- Created User model with support for both Google OAuth and Email/Password authentication
- Added `user_id` foreign keys to Account, FavoriteProduct, and Trade models
- Created initial migration that creates all tables with user relationships
- Migration automatically creates default admin user (`admin@tradelogger.local`)

**Session 2: auth-backend-session** ✅
- JWT authentication setup with access tokens (15 min) and refresh tokens (7 days)
- Google OAuth integration via Authlib
- Email/password registration and login endpoints
- Password hashing with bcrypt
- Token refresh mechanism

**Session 3: auth-protection-session** ✅
- Protected all API routes with @jwt_required decorator
- Added user_id filtering to all queries
- IDOR protection - users can only access their own resources
- Returns 403 for unauthorized access attempts

**Session 4: auth-frontend-session** ✅
- Login page with email/password form and Google OAuth button
- Auth state management via auth.js
- Automatic token refresh (every 13 minutes)
- User profile UI in navbar with logout button
- Protected web routes with login_required decorator

**Quick Overview:**
- **Mode:** Multi-user (strict auth required)
- **Methods:** Google OAuth + Email/Password
- **Token Type:** JWT with HttpOnly cookies
- **User Isolation:** Users only see their own data
- **Migration:** Existing data → default admin user

**Implementation Sessions:**
1. `auth-database-session` - User model, migrations, data migration
2. `auth-backend-session` - JWT setup, OAuth, login/register endpoints  
3. `auth-protection-session` - Route protection, user isolation, IDOR fix (SEC-013)
4. `auth-frontend-session` - Login page, Google button, auth state

---

## 📋 Authentication System Details

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│  Auth Methods                                                │
│  ├── Google OAuth (via Authlib)                             │
│  └── Email/Password + JWT                                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  JWT Token Strategy                                          │
│  ├── Access Token: 15 min (HttpOnly cookie)                 │
│  └── Refresh Token: 7 days (HttpOnly cookie)                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  User Model                                                  │
│  ├── id, email (unique), name, profile_picture              │
│  ├── auth_provider (google|email)                           │
│  ├── google_id (nullable), password_hash (nullable)         │
│  ├── is_active, created_at, updated_at                      │
│  └── relationships: trades, favorites, accounts             │
└─────────────────────────────────────────────────────────────┘
```

### Session 1: `auth-database-session`

**Goals:**
- Create User model with support for both auth methods
- Add `user_id` foreign keys to Trade, FavoriteProduct, Account
- Create database migration
- Migrate existing data to default admin user

**Files to Create/Modify:**
- `src/models.py` - Add User model, add user_id to existing models
- `migrations/` - Alembic migration script

**User Model Schema:**
```python
class User(db.Model):
    __tablename__ = "users"
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), nullable=False, unique=True)
    name = db.Column(db.String(100), nullable=False)
    profile_picture = db.Column(db.String(500), nullable=True)
    
    # Auth fields
    auth_provider = db.Column(db.String(20), nullable=False, default='email')  # 'google' | 'email'
    google_id = db.Column(db.String(100), nullable=True, unique=True)
    password_hash = db.Column(db.String(255), nullable=True)  # NULL for Google users
    
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    trades = db.relationship("Trade", backref="user", lazy=True)
    favorites = db.relationship("FavoriteProduct", backref="user", lazy=True)
    accounts = db.relationship("Account", backref="user", lazy=True)
```

**Migration Strategy:**
```python
# 1. Add nullable user_id columns to all tables
# 2. Create default admin user: email="admin@tradelogger.local", name="Admin"
# 3. Update all existing records to set user_id = admin_user.id
# 4. Make user_id columns non-nullable
# 5. Add foreign key constraints
```

**Dependencies to Add:**
```bash
alembic>=1.13.0  # Database migrations
```

---

### Session 2: `auth-backend-session`

**Goals:**
- JWT authentication setup
- Google OAuth integration
- Email/password registration & login
- Token refresh mechanism

**Files to Create:**
- `src/routes/auth.py` - Authentication routes
- `src/services/auth_service.py` - Auth business logic
- `src/utils/jwt_utils.py` - JWT token helpers
- `src/utils/password_utils.py` - Password hashing

**Configuration (add to src/config.py):**
```python
class Config:
    # ... existing config ...
    
    # JWT Config
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")  # Separate from Flask SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)
    
    # Google OAuth Config
    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:5000/auth/callback")
```

**Routes:**

```python
# src/routes/auth.py

@auth_bp.route("/auth/register", methods=["POST"])
def register():
    """Email/password registration."""
    # Validate email, password strength
    # Hash password with bcrypt
    # Create user record
    # Return success

@auth_bp.route("/auth/login", methods=["POST"])
def login():
    """Email/password login."""
    # Verify email exists
    # Check password hash
    # Generate JWT tokens
    # Set HttpOnly cookies

@auth_bp.route("/auth/google/login")
def google_login():
    """Initiate Google OAuth flow."""
    # Generate state parameter (CSRF protection)
    # Redirect to Google OAuth URL

@auth_bp.route("/auth/callback")
def google_callback():
    """Handle Google OAuth callback."""
    # Verify state parameter
    # Exchange code for tokens
    # Get user info from Google
    # Create or update user record
    # Generate JWT tokens
    # Set HttpOnly cookies

@auth_bp.route("/auth/refresh", methods=["POST"])
def refresh_token():
    """Refresh access token using refresh token."""
    # Validate refresh token
    # Generate new access token
    # Set new cookie

@auth_bp.route("/auth/logout", methods=["POST"])
def logout():
    """Clear auth cookies."""
    # Clear both cookies

@auth_bp.route("/auth/me")
@jwt_required
def get_current_user():
    """Get current user info."""
    # Return user data (no sensitive fields)
```

**JWT Token Structure:**
```python
# Access Token Payload
{
    "sub": "user_uuid",
    "email": "user@example.com",
    "type": "access",
    "iat": 1234567890,
    "exp": 1234568790  # 15 min
}

# Refresh Token Payload
{
    "sub": "user_uuid",
    "type": "refresh",
    "iat": 1234567890,
    "exp": 1235172690  # 7 days
}
```

**Dependencies to Add:**
```bash
PyJWT>=2.8.0           # JWT tokens
authlib>=1.3.0         # OAuth integration
bcrypt>=4.1.0          # Password hashing
```

---

### Session 3: `auth-protection-session`

**Goals:**
- Protect all API routes with JWT verification
- Add user_id filtering to all queries
- Fix IDOR vulnerabilities (SEC-013)

**Decorator:**
```python
# src/utils/decorators.py

def jwt_required(f):
    """Decorator to require valid JWT access token."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.cookies.get('access_token')
        if not token:
            return jsonify({"error": "Authentication required"}), 401
        
        try:
            payload = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            g.current_user_id = payload['sub']
            g.current_user_email = payload['email']
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        
        return f(*args, **kwargs)
    return decorated_function
```

**Route Updates:**

All routes need to:
1. Add `@jwt_required` decorator
2. Filter queries by `user_id = g.current_user_id`
3. Verify ownership on single-resource endpoints

```python
# Example: src/routes/trades.py

@trades_bp.route("/trades", methods=["GET"])
@jwt_required
def get_trades():
    """Get all trades for current user only."""
    filters = request.args.to_dict()
    filters['user_id'] = g.current_user_id  # Enforce user isolation
    
    result = TradeService.get_trades(filters)
    return jsonify(result)

@trades_bp.route("/trades/<trade_id>", methods=["GET"])
@jwt_required
def get_trade(trade_id):
    """Get single trade - verify ownership."""
    trade = TradeService.get_trade(trade_id)
    
    if not trade:
        return jsonify({"error": "Trade not found"}), 404
    
    # IDOR protection: verify user owns this trade
    if trade.user_id != g.current_user_id:
        return jsonify({"error": "Access denied"}), 403
    
    return jsonify(trade.to_dict())

@trades_bp.route("/trades", methods=["POST"])
@jwt_required
def create_trade():
    """Create trade - associate with current user."""
    data = request.get_json()
    data['user_id'] = g.current_user_id  # Force user association
    
    trade = TradeService.create_trade(data)
    return jsonify(trade.to_dict()), 201
```

**Files to Modify:**
- `src/routes/trades.py` - All 8 endpoints
- `src/routes/favorites.py` - All 5 endpoints
- `src/routes/accounts.py` - All 5 endpoints
- `src/routes/metrics.py` - Filter by user trades
- `src/services/trade_service.py` - Add user_id to all queries
- `src/services/` - All service files

---

### Session 4: `auth-frontend-session`

**Goals:**
- Create login page with both auth options
- Add auth state management
- Update navbar with user profile
- Handle token refresh

**Files to Create/Modify:**
- `web/templates/login.html` - Login page
- `web/static/js/auth.js` - Auth utilities
- `web/templates/base.html` - Add auth UI to navbar

**Login Page Design:**
```
┌─────────────────────────────────────┐
│           TradeLogger               │
│                                     │
│  ┌─────────────────────────────┐   │
│  │  Sign in with Google        │   │
│  └─────────────────────────────┘   │
│                                     │
│  ────────── or ──────────           │
│                                     │
│  Email: [                    ]      │
│  Password: [                 ]      │
│                                     │
│  [        Sign In         ]         │
│                                     │
│  Don't have an account? Register    │
└─────────────────────────────────────┘
```

**Auth Flow:**
```javascript
// web/static/js/auth.js

class AuthManager {
    constructor() {
        this.accessToken = null;
        this.refreshTimer = null;
        this.init();
    }
    
    init() {
        // Check auth status on page load
        this.checkAuth();
        
        // Set up token refresh (refresh at 80% of expiry time)
        this.scheduleRefresh();
    }
    
    async checkAuth() {
        const response = await fetch('/auth/me', { credentials: 'include' });
        if (!response.ok) {
            // Not authenticated, redirect to login
            if (!window.location.pathname.startsWith('/login')) {
                window.location.href = '/login?redirect=' + encodeURIComponent(window.location.pathname);
            }
        } else {
            const user = await response.json();
            this.updateUI(user);
        }
    }
    
    async refreshToken() {
        const response = await fetch('/auth/refresh', {
            method: 'POST',
            credentials: 'include'
        });
        
        if (!response.ok) {
            // Refresh failed, redirect to login
            window.location.href = '/login';
        }
    }
    
    async logout() {
        await fetch('/auth/logout', {
            method: 'POST',
            credentials: 'include'
        });
        window.location.href = '/login';
    }
}
```

**Protected Route Decorator (Python Web Routes):**
```python
# web/routes/__init__.py

def login_required(f):
    """Require authentication for web routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.cookies.get('access_token')
        if not token:
            return redirect(url_for('web.login', redirect=request.path))
        
        try:
            payload = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            g.current_user_id = payload['sub']
        except jwt.ExpiredSignatureError:
            return redirect(url_for('web.login', redirect=request.path))
        except jwt.InvalidTokenError:
            return redirect(url_for('web.login', redirect=request.path))
        
        return f(*args, **kwargs)
    return decorated_function

# Apply to all web routes
@web_bp.route("/")
@login_required
def dashboard():
    return render_template("dashboard.html")
```

---

### Environment Variables Required

```bash
# Required for auth system
JWT_SECRET_KEY=your-super-secret-jwt-key-min-32-chars

# For Google OAuth (optional if only using email/password)
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:5000/auth/callback

# Existing vars
SECRET_KEY=your-flask-secret-key
DATABASE_URL=postgresql://...
```

---

### Google OAuth Setup Instructions

1. **Go to Google Cloud Console:** https://console.cloud.google.com/
2. **Create a new project** (or use existing)
3. **Enable Google+ API** (or Google Identity Toolkit API)
4. **Create OAuth 2.0 credentials:**
   - Application type: Web application
   - Authorized redirect URIs: `http://localhost:5000/auth/callback`
   - (Add production URI when deploying)
5. **Copy Client ID and Secret** to environment variables

---

### Testing Checklist

- [ ] User can register with email/password
- [ ] User can login with email/password
- [ ] User can login with Google OAuth
- [ ] JWT tokens are stored in HttpOnly cookies
- [ ] Token refresh works automatically
- [ ] Unauthenticated users are redirected to login
- [ ] Users only see their own trades/favorites
- [ ] Cannot access other users' resources (IDOR test)
- [ ] Logout clears cookies
- [ ] Existing data is assigned to admin user
- [ ] Passwords are properly hashed (not stored plaintext)

---

### SEC-002 through SEC-005

**Implementation Session:** `security-headers-session`

---

### SEC-002: Insecure CORS Configuration
**Risk:** Cross-origin attacks from any website, CSRF bypass

**File:** `src/app.py` Line 27

**Current Code:**
```python
CORS(app, resources={r"/api/*": {"origins": "*"}})
```

**Fix:**
```python
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5000", "http://localhost:3000"],
        "supports_credentials": True
    }
})
```

**Implementation Session:** `security-headers-session`

---

### SEC-003: Missing Security Headers
**Risk:** XSS attacks, clickjacking, MIME-type sniffing attacks

**File:** `src/app.py`

**Missing Headers:**
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- X-XSS-Protection: 1; mode=block
- Strict-Transport-Security
- Content-Security-Policy
- Referrer-Policy

**Fix:** Add after_request handler or use Flask-Talisman

**Implementation Session:** `security-headers-session`

---

### SEC-004: Weak Default Secret Key
**Risk:** Session hijacking, cookie forgery

**File:** `src/config.py` Line 11

**Current Code:**
```python
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
```

**Fix:**
```python
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable must be set")
```

**Implementation Session:** `security-headers-session`

---

### SEC-005: No CSRF Protection
**Risk:** Cross-Site Request Forgery attacks

**Files:** All form submissions

**Fix:** Add Flask-WTF CSRF protection

**Implementation Session:** `csrf-protection-session`

---

## 🔴 HIGH SEVERITY (Fix Within 48 Hours)

### SEC-006: Path Traversal in Screenshot Serving
**Risk:** Unauthorized file access, information disclosure

**File:** `src/routes/trades.py` Lines 15-21

**Fix Strategy:**
- Validate filename pattern (UUID only)
- Use secure_filename
- Verify resolved path is within screenshot_dir

**Implementation Session:** `input-validation-session`

---

### SEC-007: Unrestricted File Upload
**Risk:** Remote code execution, malware upload

**File:** `src/services/trade_service.py` Lines 204-211

**Fix Strategy:**
- Validate file size (max 5MB)
- Verify file type by content (imghdr)
- Check file extension
- Add allowed extensions whitelist

**Implementation Session:** `input-validation-session`

---

### SEC-008: No Rate Limiting
**Risk:** DoS attacks, brute force, resource exhaustion

**Files:** All API routes

**Fix Strategy:**
- Add Flask-Limiter
- Set default limits (200/day, 50/hour)
- Stricter limits for POST/PUT/DELETE (10/minute)

**Implementation Session:** `rate-limiting-session`

---

### SEC-009: SQL Injection via Date Filters
**Risk:** Database compromise

**File:** `src/services/trade_service.py` Lines 231-234

**Fix Strategy:**
- Validate date format before using in queries
- Use datetime parsing with validation

**Implementation Session:** `input-validation-session`

---

## 🟡 MEDIUM SEVERITY (Fix Within 1 Week)

### SEC-010: Information Disclosure in Error Messages
**Risk:** System information leakage

**File:** `src/app.py` Line 82

**Current Code:**
```python
app.run(debug=True, host="0.0.0.0", port=5000)
```

**Fix:** Remove debug=True or make it environment-dependent

**Implementation Session:** `error-handling-session`

---

### SEC-011: Missing Input Validation on Notes Field
**Risk:** XSS via stored payload

**Files:** 
- `src/models.py`
- `web/templates/trades.html` Line 378

**Fix Strategy:**
- Use bleach library to sanitize HTML
- Allow only safe tags (b, i, u, strong, em, br)

**Implementation Session:** `xss-protection-session`

---

### SEC-012: Electron Security Issues
**Risk:** Remote code execution via Electron

**File:** `desktop/main.js` Lines 28-31

**Current Code:**
```javascript
nodeIntegration: true,
contextIsolation: false,
```

**Fix:**
```javascript
nodeIntegration: false,
contextIsolation: true,
sandbox: true,
```

**Implementation Session:** `electron-security-session`

---

### SEC-013: Insecure Direct Object References (IDOR) ✅ FIXED
**Risk:** Access to other users' trades

**Status:** ✅ RESOLVED - Fixed in auth-protection-session

**Fix:**
- All API routes now require authentication (@jwt_required)
- Service layer verifies resource ownership before returning data
- Returns 403 Forbidden if user attempts to access another user's resources
- All queries filtered by current_user_id from JWT token

---

### SEC-014: Docker Compose Exposes Database Publicly
**Risk:** Database exposed to internet

**File:** `docker-compose.yml` Lines 8-9

**Fix Strategy:**
- Remove ports or restrict to 127.0.0.1 only
- Or use internal Docker network only

**Implementation Session:** `docker-security-session`

---

## 🟢 LOW SEVERITY (Fix When Convenient)

### SEC-015: Missing Security Headers in Nginx
**File:** `nginx.conf`

**Fix:** Add security headers, disable server_tokens

**Implementation Session:** `nginx-security-session`

---

### SEC-016: Missing Input Length Validation
**Files:** All string input fields

**Fix Strategy:**
- Add marshmallow schemas for validation
- Set max lengths (symbol: 50, notes: 5000)

**Implementation Session:** `input-validation-session`

---

### SEC-017: No Audit Logging
**Risk:** Cannot detect or investigate security incidents

**Files:** All mutation endpoints

**Fix Strategy:**
- Create audit logger
- Log all CREATE, UPDATE, DELETE actions
- Include user_id, IP, timestamp, resource details

**Implementation Session:** `audit-logging-session`

---

## 📋 Implementation Roadmap

### Phase 1: Critical Security (Week 1-2)
**Auth System (Priority 1):**
1. `auth-database-session` - User model, migrations, data migration (SEC-001 baseline)
2. `auth-backend-session` - JWT setup, OAuth, login/register endpoints
3. `auth-protection-session` - Route protection, user isolation, IDOR fix (SEC-013)
4. `auth-frontend-session` - Login page, Google button, auth state

**Security Headers:**
5. `security-headers-session` - SEC-002, SEC-003, SEC-004
6. `csrf-protection-session` - SEC-005

### Phase 2: High Priority (Week 3)
**Sessions:**
7. `input-validation-session` - SEC-006, SEC-007, SEC-009, SEC-016
8. `rate-limiting-session` - SEC-008

### Phase 3: Medium Priority (Week 4)
**Sessions:**
9. `error-handling-session` - SEC-010
10. `xss-protection-session` - SEC-011
11. `electron-security-session` - SEC-012
12. `docker-security-session` - SEC-014

### Phase 4: Low Priority & Hardening (Week 5)
**Sessions:**
13. `nginx-security-session` - SEC-015
14. `audit-logging-session` - SEC-017

---

## 🧪 Testing Checklist Per Session

Each session should include:
- [ ] Unit tests for new security functions
- [ ] Integration tests for protected endpoints
- [ ] Security test cases (attempted bypasses)
- [ ] Manual verification
- [ ] Update documentation

---

## 📊 Dependencies to Add

### Core Auth Dependencies
```
# JWT Authentication
PyJWT>=2.8.0

# Google OAuth
authlib>=1.3.0

# Password Hashing
bcrypt>=4.1.0

# Database Migrations
alembic>=1.13.0
```

### Security Dependencies
```
# CSRF Protection
flask-wtf>=1.0.0

# Rate Limiting
flask-limiter>=3.0.0

# Input Sanitization
bleach>=6.0.0

# Validation
marshmallow>=3.20.0

# Security Headers (optional)
flask-talisman>=1.0.0

# Security Scanning (dev)
bandit>=1.7.0
safety>=2.0.0
```

---

## 🔍 Security Testing Commands

```bash
# Static analysis
bandit -r src/ -f json -o bandit-report.json

# Dependency check
safety check --json --output safety-report.json

# Run security-focused tests
pytest tests/ -k "security" -v
```

---

## 📝 Notes

- Each session should create a feature branch: `security/session-name`
- All changes must be tested before merging
- Update this plan as issues are resolved
- Document any security decisions or trade-offs
