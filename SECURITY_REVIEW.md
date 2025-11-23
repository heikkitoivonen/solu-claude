# Security Review Report

**Date**: 2025-11-23
**Reviewer**: Claude Code
**Overall Assessment**: GOOD with some recommendations

## Executive Summary

The codebase demonstrates strong security practices overall, particularly in authentication and input validation. CSRF protection is properly implemented, passwords are securely hashed, and SQL injection vulnerabilities are prevented through ORM usage. However, there are several critical issues that need immediate attention, particularly around the hardcoded secret key and XSS vulnerabilities in the JavaScript code.

**Risk Level**: MEDIUM (reducible to LOW with recommended fixes)

---

## 🔴 CRITICAL ISSUES (Must Fix Immediately)

### 1. **Hardcoded Secret Key in Production**
**Location**: `app/__init__.py:21`
**Severity**: CRITICAL

```python
app.config["SECRET_KEY"] = "dev-secret-key-change-in-production"
```

**Issue**: The secret key is hardcoded and identical across all deployments. This key is used for:
- Session signing
- CSRF token generation
- Password reset tokens (if implemented)

**Attack Vector**: An attacker who knows this key can:
- Forge session cookies and impersonate any user
- Bypass CSRF protection
- Potentially decrypt session data

**Fix**:
```python
import os
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or "dev-secret-key-change-in-production"
```

Then in production:
```bash
export SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
```

**Priority**: FIX BEFORE PRODUCTION DEPLOYMENT

---

### 2. **XSS Vulnerability in Multiple Results Display**
**Location**: `app/static/js/app.js:70-84`, `admin.js:87-98, 108-123`
**Severity**: HIGH

**Issue**: User-controlled data is inserted into HTML using template literals without sanitization:

```javascript
// app.js line 76-80
resultsList.innerHTML = results.map((result, index) => {
    return `
        <div class="result-card" onclick="selectResult(${index})">
            <h3>${resource.name}</h3>  // ❌ XSS vulnerability
            <div class="result-meta">
                <span class="type">Type: ${resource.type}</span>  // ❌ XSS vulnerability
```

```javascript
// admin.js line 90-91
<strong>${fp.name}</strong>  // ❌ XSS vulnerability
<small>${fp.image_filename}</small>  // ❌ XSS vulnerability
```

**Attack Vector**: An admin could create a resource named:
```
<img src=x onerror="alert(document.cookie)">
```

When searched or displayed, this would execute JavaScript in the context of other users' browsers.

**Fix Options**:

**Option 1**: Use `textContent` instead of `innerHTML`:
```javascript
const card = document.createElement('div');
card.className = 'result-card';
const h3 = document.createElement('h3');
h3.textContent = resource.name;  // ✅ Safe
card.appendChild(h3);
```

**Option 2**: Create an HTML sanitization function:
```javascript
function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Then use:
<h3>${escapeHtml(resource.name)}</h3>
```

**Priority**: HIGH - Fix before allowing untrusted admin users

---

### 3. **Open Redirect Vulnerability**
**Location**: `app/auth_routes.py:79-80`
**Severity**: MEDIUM-HIGH

```python
next_page = request.args.get("next")
return redirect(next_page if next_page else url_for("main.admin"))
```

**Issue**: The `next` parameter is not validated, allowing attackers to redirect users to external sites.

**Attack Vector**:
```
https://yoursite.com/login?next=https://evil.com/phishing
```

After successful login, users would be redirected to the attacker's site.

**Fix**:
```python
from urllib.parse import urlparse, urljoin
from flask import request

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

next_page = request.args.get("next")
if next_page and not is_safe_url(next_page):
    next_page = None
return redirect(next_page if next_page else url_for("main.admin"))
```

**Priority**: HIGH

---

## 🟡 HIGH PRIORITY ISSUES

### 4. **Unrestricted File Upload**
**Location**: `app/routes.py:69-100`
**Severity**: MEDIUM-HIGH

**Issues**:
1. No file size limit - allows DoS through disk exhaustion
2. No authentication required for the `/api/floorplans` POST endpoint
3. Files saved with predictable names (timestamp-based)
4. SVG files allowed without sanitization (can contain malicious JavaScript)

**Current Code**:
```python
@main.route("/api/floorplans", methods=["GET", "POST"])
def floorplans() -> Response | tuple[Response, int]:
    if request.method == "POST":
        # No authentication check! ❌
        file = request.files["image"]
        # No size limit! ❌
```

**Fixes**:

1. **Add authentication**:
```python
@main.route("/api/floorplans", methods=["GET", "POST"])
@login_required  # ✅ Add this
def floorplans() -> Response | tuple[Response, int]:
```

2. **Add file size limit**:
```python
# In app/__init__.py
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit
```

3. **Validate file content** (not just extension):
```python
import imghdr

def validate_image(stream):
    header = stream.read(512)
    stream.seek(0)
    format = imghdr.what(None, header)
    if not format:
        return None
    return '.' + format in ALLOWED_EXTENSIONS
```

4. **Consider removing SVG** from allowed types or sanitize them, as SVGs can contain `<script>` tags.

**Priority**: HIGH

---

### 5. **Missing Rate Limiting**
**Location**: All authentication endpoints
**Severity**: MEDIUM

**Issue**: No rate limiting on:
- Login attempts (`/login`)
- Password changes (`/change-password`)
- User creation (`/admin/users/create`)

**Attack Vector**: Brute force attacks on passwords, even with strong password requirements.

**Fix**: Install and configure Flask-Limiter:
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

@auth.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")  # ✅ Add this
def login():
```

**Priority**: HIGH for production

---

### 6. **SQL Injection via ilike() - False Alarm (Actually Safe)**
**Location**: `app/routes.py:38`
**Severity**: NONE (informational)

```python
resources = Resource.query.filter(Resource.name.ilike(f"%{query}%")).all()
```

**Analysis**: While this looks vulnerable, SQLAlchemy properly parameterizes this query. The `ilike()` method uses bound parameters, not string concatenation. However, for clarity and to avoid confusion:

**Better Practice** (optional):
```python
# More explicit parameterization
resources = Resource.query.filter(
    Resource.name.ilike(f"%{query}%")
).all()
```

This is **already safe** but the code review flags it for awareness.

**Priority**: INFORMATIONAL

---

## 🟢 MEDIUM PRIORITY ISSUES

### 7. **Debug Mode Enabled**
**Location**: `run.py:6`
**Severity**: MEDIUM

```python
app.run(debug=True, host="127.0.0.1", port=8000)
```

**Issue**: Debug mode:
- Exposes detailed stack traces with source code
- Enables the Werkzeug debugger (remote code execution if PIN is guessed)
- Disables many security features

**Fix**:
```python
import os
debug_mode = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
app.run(debug=debug_mode, host="127.0.0.1", port=8000)
```

**Priority**: CRITICAL for production, OK for development

---

### 8. **Deprecated datetime.utcnow()**
**Location**: `app/models.py:17, 45, 69`
**Severity**: LOW (future compatibility)

```python
created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

**Issue**: `datetime.utcnow()` is deprecated in Python 3.14 and will be removed.

**Fix**:
```python
from datetime import datetime, timezone

created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
```

**Priority**: LOW (will cause warnings, not security issue)

---

### 9. **Weak Session Cookie Configuration**
**Location**: `app/__init__.py` (missing configuration)
**Severity**: MEDIUM

**Missing Security Headers**:
```python
# Add to create_app()
app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS only
app.config['SESSION_COOKIE_HTTPONLY'] = True  # No JavaScript access
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour
```

**Priority**: MEDIUM (HIGH for production)

---

### 10. **Missing Security Headers**
**Location**: Missing from entire application
**Severity**: MEDIUM

**Missing Headers**:
- `Content-Security-Policy`
- `X-Frame-Options`
- `X-Content-Type-Options`
- `Strict-Transport-Security`

**Fix**: Use Flask-Talisman:
```python
from flask_talisman import Talisman

Talisman(app,
    force_https=True,
    strict_transport_security=True,
    content_security_policy={
        'default-src': "'self'",
        'script-src': "'self'",
        'style-src': "'self' 'unsafe-inline'",
        'img-src': "'self' data:",
    }
)
```

**Priority**: MEDIUM (HIGH for production)

---

### 11. **Information Disclosure in Error Messages**
**Location**: `app/auth_routes.py:82`
**Severity**: LOW

```python
flash("Invalid username or password", "error")
```

**Good Practice**: The error message doesn't distinguish between invalid username and invalid password. This is correct and prevents username enumeration.

**However**: User creation at line 174 reveals if username exists:
```python
if User.query.filter_by(username=username).first():
    flash(f"User '{username}' already exists", "error")
```

This allows username enumeration. Consider:
```python
flash("Unable to create user", "error")
```

**Priority**: LOW (only admins can create users)

---

## ✅ SECURITY STRENGTHS

### Excellent Practices:

1. **✅ Strong Password Requirements**
   - Minimum 10 characters
   - Complexity requirements enforced
   - Password reuse prevention
   - Mandatory password changes for new accounts

2. **✅ CSRF Protection**
   - Flask-WTF CSRF enabled globally
   - Tokens properly included in all forms
   - API endpoints protected

3. **✅ Password Hashing**
   - Werkzeug's secure password hashing (pbkdf2:sha256)
   - Never stores plaintext passwords
   - Proper use of `check_password_hash()`

4. **✅ SQL Injection Prevention**
   - Uses SQLAlchemy ORM throughout
   - No raw SQL queries
   - Proper use of query methods

5. **✅ Authentication Flow**
   - Flask-Login properly configured
   - `@login_required` decorator used correctly
   - Admin privilege checks on sensitive operations

6. **✅ Input Validation**
   - File extension validation
   - Filename sanitization with `secure_filename()`
   - Form field validation

7. **✅ Secure File Handling**
   - Timestamps added to filenames to prevent overwrites
   - Files stored outside web root (in /static but controlled)

8. **✅ Database Security**
   - Foreign key constraints enforced
   - Cascade deletes configured properly
   - No direct user input in queries

9. **✅ Error Handling**
   - Consistent error messages
   - No stack traces exposed to users (in production mode)

10. **✅ Type Safety**
    - Comprehensive type hints throughout
    - Mypy type checking enabled

---

## 📋 RECOMMENDATIONS BY PRIORITY

### Before Production Deployment (CRITICAL):
1. ✅ Change SECRET_KEY to environment variable
2. ✅ Fix open redirect vulnerability
3. ✅ Add authentication to file upload endpoints
4. ✅ Fix XSS vulnerabilities in JavaScript
5. ✅ Disable debug mode
6. ✅ Configure secure session cookies
7. ✅ Add security headers

### High Priority:
8. ✅ Add rate limiting to authentication endpoints
9. ✅ Implement file size limits
10. ✅ Add file content validation
11. ✅ Consider removing or sanitizing SVG uploads

### Medium Priority:
12. ✅ Fix deprecated `datetime.utcnow()`
13. ✅ Add logging for security events
14. ✅ Implement account lockout after failed logins
15. ✅ Add Content-Security-Policy

### Nice to Have:
16. ✅ Add security.txt file
17. ✅ Implement HTTPS redirect
18. ✅ Add request ID tracking
19. ✅ Set up security monitoring/alerting

---

## 🔍 CODE CONSISTENCY REVIEW

### Good Consistency:
- ✅ Consistent error handling patterns
- ✅ Consistent use of type hints
- ✅ Consistent code formatting
- ✅ Consistent naming conventions
- ✅ Consistent file structure

### Minor Inconsistencies:

1. **Mixed redirect patterns**:
   - Some use `redirect(url_for(...))`
   - Some return Response type hints
   - **Recommendation**: Both are correct; maintain current usage

2. **Return type annotations**:
   - `str | Response` used consistently in auth_routes.py
   - `Response | tuple[Response, int]` in routes.py for API endpoints
   - **Recommendation**: This is correct and intentional

3. **Error response format**:
   - HTML forms use flash messages
   - API endpoints return JSON
   - **Recommendation**: This is correct and appropriate

---

## 📊 SECURITY METRICS

| Category | Score | Notes |
|----------|-------|-------|
| Authentication | 8/10 | Strong, but needs rate limiting |
| Authorization | 9/10 | Proper checks throughout |
| Input Validation | 7/10 | Good, but XSS issues in JS |
| Cryptography | 8/10 | Good hashing, but hardcoded key |
| Error Handling | 8/10 | Consistent and secure |
| Session Management | 6/10 | Missing secure cookie flags |
| File Upload | 5/10 | No auth, no size limits |
| API Security | 7/10 | CSRF protected, needs auth |
| **Overall** | **7.3/10** | **GOOD** with fixable issues |

---

## 🎯 IMMEDIATE ACTION ITEMS

1. Create `.env.example` file with placeholder for SECRET_KEY
2. Update `.gitignore` to exclude `.env`
3. Fix XSS vulnerabilities in app.js and admin.js
4. Add `@login_required` to file upload endpoints
5. Implement `is_safe_url()` function for redirect validation
6. Create production deployment checklist with security items

---

## 📝 CONCLUSION

This codebase demonstrates **strong security fundamentals** with particularly good practices in:
- Password security
- CSRF protection
- SQL injection prevention
- Authentication flow

The critical issues are **easily fixable** and primarily relate to:
- Configuration (hardcoded secrets)
- Input/output sanitization (XSS)
- Missing authentication on certain endpoints

**Recommendation**: Address all CRITICAL and HIGH priority issues before any production deployment. The codebase structure is solid and follows best practices; the issues found are typical of development-stage code and should not prevent deployment once fixed.

**Estimated Time to Fix Critical Issues**: 2-4 hours

---

**Reviewed by**: Claude Code
**Review Date**: 2025-11-23
**Next Review**: After implementing recommended fixes
