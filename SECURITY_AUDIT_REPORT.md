# OOREP Security Audit Report

**Date:** 2026-06-24  
**Auditor:** Automated Security Code Review  
**Scope:** OOREP homeopathic repertory project — 143+ Python modules, Next.js portal, Hermes bridge  
**Project Path:** `/home/walker/projects/oorep-local-repertory/`

---

## Executive Summary

This audit identified **27 security findings** across the OOREP codebase, ranging from Critical to Low severity. The most severe issues are:

1. **Unencrypted PHI at rest** — all SQLite databases containing patient health information (prescriptions, SOAP notes, audit logs, PHI mappings) are stored in plaintext with no encryption
2. **Weak predictable access tokens** in the patient portal — tokens are derived from case_id prefixes and dates
3. **Information disclosure** — the mobile API leaks internal exception messages to clients
4. **No authentication or authorization** on the mobile API — any caller can retrieve patient timelines and create consultations
5. **Insecure cookies** — the Next.js admin session cookie has `secure: false`

The codebase does demonstrate good security practices in several areas: parameterized SQL queries are used consistently, no `eval`/`exec`/`pickle`/unsafe YAML deserialization was found, the audit trail uses hash-chaining, and a PHI scrubber exists. The gaps are primarily in encryption, authentication, and API security.

---

## Findings by Severity

### CRITICAL

#### C-01: Unencrypted PHI at Rest in All SQLite Databases
**Files:** 
- `oorep/patient_file_system.py` (lines 46, 63-64, 71)
- `scripts/remedy_feedback.py` (line 27, 141)
- `oorep/audit_trail.py` (line 37, 67)
- `oorep/phi_scrubber.py` (line 37, 120)
- `oorep/soap_assembler.py` (line 40, 83)
- `oorep/private_rubrics.py` (line 47)
- `oorep/billing_integration.py` (line 20)
- `oorep/appointment_scheduler.py` (line 19)
- `oorep/red_flag_detector.py` (line 27)
- `skills/oorep-hermes-bridge/scripts/case_memory.py` (line 23)

**Severity:** CRITICAL  
**Description:** Every SQLite database in the project stores Protected Health Information (PHI) — patient pseudonyms, dates of birth, prescriptions, SOAP notes, clinical outcomes, chief complaints, follow-up reports, billing data — entirely in plaintext. There is no encryption at rest. The `CloudSyncManager` (line 79) explicitly states encryption is "planned" but not implemented (`"algorithm": "AES-256-GCM (planned)"`). Anyone with filesystem access (disk theft, backup leak, cloud snapshot exposure) can read all patient data directly.

**Recommended Fix:** 
- Use SQLCipher (`pysqlcipher3` or `sqlcipher3-binary`) for transparent full-database encryption
- Alternatively, use application-layer encryption with `cryptography.fernet` for sensitive fields before INSERT
- At minimum, encrypt the `data/` directory at the filesystem level (LUKS, eCryptfs)
- Implement the encryption described in `cloud_sync_manager.py:get_encryption_info()` — it is currently a stub

---

#### C-02: No Authentication or Authorization on Mobile API
**File:** `oorep/mobile_api.py` (lines 33-184)  
**Severity:** CRITICAL  
**Description:** The `OOREPApp` class defines 9 API routes including patient data access (`GET /api/patient/{pseudonym}`), patient timeline retrieval (`GET /api/patient/{pseudonym}/timeline`), and consultation creation (`POST /api/patient/{pseudonym}/consultation`). None of these routes have any authentication, authorization, or access control. Any network client can:
- Retrieve any patient's complete case timeline (prescriptions, consultations, SOAP notes)
- Create new consultations for any patient
- Access all repertorization data

The class docstring (line 7) claims "CORS-enabled" but no CORS middleware is actually implemented — the `cors: True` flag on line 181 is just metadata, not enforcement.

**Recommended Fix:**
- Add authentication middleware (JWT bearer token, API key, or session-based auth)
- Implement role-based access control (practitioner vs. patient vs. admin)
- Add actual CORS headers configuration when integrating with a web framework
- Rate-limit all endpoints
- Validate that the requesting user has permission to access the requested patient's data

---

#### C-03: Weak Predictable Patient Portal Access Tokens
**File:** `oorep/patient_portal.py` (lines 77-88)  
**Severity:** CRITICAL  
**Description:** The `validate_access_token` method (line 77) validates tokens using a trivially predictable scheme:
```python
expected = f"portal_{case_id[:8]}"
return token.startswith(expected)
```
And `generate_access_token` (line 86) produces:
```python
return f"portal_{case_id[:8]}_{datetime.utcnow().strftime('%y%m%d')}"
```
This is completely insecure:
1. The token is derived from the case_id, which may be known or guessable
2. `startswith()` validation means any string prefixed with `portal_{case_id[:8]}` passes — an attacker can append anything
3. The date component (`%y%m%d`) is trivially predictable
4. No cryptographic randomness, no HMAC, no expiration check, no server-side token store
5. The comment on line 82 acknowledges: "In production, this would check against a secure token store"

**Recommended Fix:**
- Generate tokens using `secrets.token_urlsafe(32)` (cryptographic randomness)
- Store tokens server-side with expiration timestamps
- Validate using constant-time comparison (`hmac.compare_digest`)
- Implement proper token expiration and revocation

---

### HIGH

#### H-01: Information Disclosure via API Error Responses
**File:** `oorep/mobile_api.py` (lines 80, 92, 104, 114, 124, 144, 161)  
**Severity:** HIGH  
**Description:** Every API route handler catches exceptions and returns `str(exc)` directly to the client:
```python
except Exception as exc:
    return self._error(str(exc), 500)
```
This leaks internal implementation details — file paths, database errors, stack trace fragments, SQL errors, internal module names — to API consumers. For a healthcare system, this could expose:
- Database schema details (SQLite error messages)
- File system paths (`FileNotFoundError` messages)
- Internal class/method names
- Potential PHI in error messages

**Recommended Fix:**
- Log full exceptions server-side (`logging.exception()`)
- Return generic error messages to clients (`"Internal server error"`, `"Resource not found"`)
- Use error codes/IDs that map to detailed logs without exposing details

---

#### H-02: Insecure Admin Session Cookie (secure: false)
**File:** `oorep-case-portal/src/app/api/admin/auth/route.ts` (lines 20, 34)  
**Severity:** HIGH  
**Description:** The admin session cookie is set with `secure: false`:
```typescript
res.cookies.set("admin_session", token, { httpOnly: true, secure: false, sameSite: "lax", path: "/" });
```
This means the session cookie can be transmitted over unencrypted HTTP, making it vulnerable to man-in-the-middle attacks. An attacker on the same network can intercept the admin session token and gain full administrative access to the case portal, which contains patient case data.

**Recommended Fix:**
- Set `secure: true` (or at minimum `secure: process.env.NODE_ENV === "production"`)
- Ensure the portal is only served over HTTPS
- Consider adding `__Host-` prefix to the cookie name for additional security

---

#### H-03: No Session Expiration for Admin Portal
**File:** `oorep-case-portal/src/lib/adminAuth.ts` (lines 56-80)  
**Severity:** HIGH  
**Description:** The `createAdminSession()` function (line 56) stores sessions with a `createdAt` timestamp but `requireAdminSession()` (line 73) never checks session age. Sessions persist indefinitely until manually destroyed. The `RESUME.md` file (line 84) acknowledges this as a known gap: "Session expiry warning/redirect" is a TODO.

Additionally, sessions are stored in a plaintext JSON file (`SESSION_FILE`, line 10) with no file permissions set — any process/user can read or modify the session store.

**Recommended Fix:**
- Add session expiration check (e.g., 8-hour timeout) in `requireAdminSession()`
- Set restrictive file permissions on the session file (0600)
- Consider using an in-memory session store or encrypted database table
- Implement session rotation on privilege change

---

#### H-04: SQL Injection via String Formatting in outcome_predictor_stats.py
**File:** `oorep/outcome_predictor_stats.py` (lines 118-122)  
**Severity:** HIGH  
**Description:** The `_load_data` method constructs a SQL query using f-string interpolation with the `predictor` parameter:
```python
c.execute(f"""
    SELECT {predictor}, outcome_score
    FROM prescriptions
    WHERE {predictor} IS NOT NULL AND outcome_score IS NOT NULL
""")
```
While there is a whitelist check on line 112 (`valid_predictors = {"rubric_coverage", "keynote_match", "composite_score"}`), the f-string interpolation still injects the value directly into the SQL. If the whitelist check is ever removed, modified, or bypassed (e.g., by a future developer who doesn't understand the security implication), this becomes a direct SQL injection vector. The `predictor` value is used in both the SELECT and WHERE clauses.

**Recommended Fix:**
- Use a mapping/enum approach that translates validated input to hardcoded SQL constants
- Never interpolate column names via f-strings, even with a whitelist
- Use `sqlalchemy` or similar with proper identifier quoting if dynamic columns are needed

---

#### H-05: SQL Injection in patient_cohort_analytics.py via .format()
**File:** `oorep/patient_cohort_analytics.py` (lines 236-239)  
**Severity:** HIGH  
**Description:** The `monthly_volume` method uses `.format()` to interpolate the `months` parameter directly into SQL:
```python
sql = '''
    ...
    WHERE substr(prescribed_date, 1, 7) >= date('now', '-{} months')
    ...
'''.format(months)
rows = self._execute(sql)
```
The `months` parameter is an integer with a default of 12, but there is no validation that it is actually an integer before interpolation. If a caller passes a string, this becomes SQL injection. The `date('now', '-{} months')` SQLite function argument is interpolated without parameterization.

**Recommended Fix:**
- Validate `months` is an integer and within reasonable bounds
- Use parameterized query: `date('now', '-' || ? || ' months')` with `(months,)` as parameter
- Or use Python to compute the date and pass it as a parameter

---

#### H-06: Dynamic SQL Column Names in UPDATE Statements (Indirect Injection Risk)
**Files:**
- `oorep/patient_file_system.py` (lines 231, 237, 441, 447)
- `oorep/analysis_manager.py` (lines 312, 318)

**Severity:** HIGH  
**Description:** Multiple UPDATE statements construct column names dynamically:
```python
# patient_file_system.py line 231:
set_clause = ", ".join(f"{k} = ?" for k in fields)
# line 237:
cursor.execute(f"UPDATE patients SET {set_clause} WHERE pseudonym = ?", values)
```
While the keys are filtered through an `allowed` set (line 225: `allowed = {"gender", "date_of_birth", "status", "notes", "contact_consent"}`), the column names are still interpolated into SQL via f-string. If the `allowed` set is ever extended to include user-controlled values, or if the filtering logic is changed, this becomes SQL injection. The `update_consultation` method (line 427) uses a blocklist approach (`blocked = {"consultation_id", "patient_pseudonym", "created_at"}`) which is weaker — any key NOT in the blocklist is accepted, meaning new columns added to the schema would be writable.

**Recommended Fix:**
- Use parameterized identifier quoting or a strict whitelist mapping
- For `update_consultation`, switch from blocklist to allowlist approach
- Validate all field names against a hardcoded schema before interpolation

---

#### H-07: Path Traversal in voice_to_text_audio_import.py
**File:** `oorep/voice_to_text_audio_import.py` (lines 26-35)  
**Severity:** HIGH  
**Description:** The `import_audio` method accepts an arbitrary `audio_path` parameter and resolves it without validation:
```python
def import_audio(self, audio_path: str, case_id: str, ...):
    path = Path(audio_path)
    if not path.exists():
        return {"error": f"Audio file not found: {audio_path}"}
    record = {
        ...
        "audio_path": str(path.resolve()),
        ...
    }
```
The resolved absolute path is stored in the JSON record and returned to the caller. An attacker can:
1. Supply `../../../etc/passwd` or any arbitrary path to confirm file existence (information disclosure)
2. Have the resolved absolute path of any file on the system stored in the record (path disclosure)
3. The `case_id` parameter is also used directly in filename construction: `f"{record['import_id']}.json"` — while `import_id` is generated internally, `case_id` is stored without validation

The `list_imports` method (line 169) reads all JSON files from `imports_dir` without validation.

**Recommended Fix:**
- Validate that `audio_path` is within an allowed directory
- Restrict to specific file extensions (`.wav`, `.mp3`, `.m4a`, `.ogg`, `.flac` — already listed in `get_supported_formats()`)
- Sanitize `case_id` to prevent path traversal in filename construction
- Use `os.path.realpath()` and compare against a base directory

---

#### H-08: Unvalidated User Input in Multiple Patient Data Functions
**Files:**
- `oorep/patient_file_system.py` — `create_patient()` (line 141), `update_patient()` (line 218), `create_consultation()` (line 295)
- `oorep/billing_integration.py` — `create_invoice()` (line 46)
- `oorep/appointment_scheduler.py` — `schedule()` (line 44)

**Severity:** HIGH  
**Description:** Multiple functions accept dictionaries of user-provided data and store them in the database with minimal validation:
- `create_patient`: Only validates `pseudonym` is non-empty; `date_of_birth`, `notes` stored as-is
- `create_consultation`: `chief_complaint`, `practitioner_id`, `outcome_notes` stored without length limits or sanitization
- `create_invoice`: `case_id`, `insurance_code`, `notes` stored without validation
- `schedule`: `case_id`, `appointment_type`, `notes` stored without validation

While SQL injection is mitigated by parameterized queries, there is no validation of:
- Input length (potential DoS via very long strings)
- Input format (e.g., `date_of_birth` should be a valid date)
- Input content (e.g., `practitioner_id` should match a known practitioner)
- Malicious content in free-text fields

**Recommended Fix:**
- Add input validation for all user-facing fields (type, length, format)
- Use Pydantic models or similar for request validation
- Enforce maximum string lengths
- Validate date formats with `datetime.strptime`

---

### MEDIUM

#### M-01: Unsafe os.system() Call in PDF Route
**File:** `oorep-case-portal/src/app/api/admin/pdf/route.ts` (line 66)  
**Severity:** MEDIUM  
**Description:** The dynamically-generated Python script (embedded as a template string) uses `os.system("uv pip install fpdf2")` to install a package at runtime. While this runs within a `python3 -c` subprocess and requires admin auth, `os.system()` is inherently unsafe (shell metacharacter injection if the package name is ever parameterized). Additionally, installing packages at runtime is a supply-chain risk and can fail unpredictably.

**Recommended Fix:**
- Use `subprocess.run([sys.executable, "-m", "pip", "install", "fpdf2"], check=True)` instead of `os.system()`
- Pre-install `fpdf2` as a dependency rather than installing at runtime
- Pin the package version to prevent supply-chain attacks

---

#### M-02: Hardcoded Default Database Path Leaks System Structure
**Files:**
- `oorep/patient_file_system.py` (line 46)
- `oorep/audit_trail.py` (line 37)
- `oorep/phi_scrubber.py` (line 37)
- `oorep/soap_assembler.py` (line 40)
- `oorep/red_flag_detector.py` (line 27)
- `oorep/analysis_manager.py` (line 52)
- `skills/oorep-hermes-bridge/scripts/oorep_bridge.py` (line 27)
- `skills/oorep-hermes-bridge/scripts/case_memory.py` (line 23)

**Severity:** MEDIUM  
**Description:** Multiple modules hardcode filesystem paths:
```python
DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "feedback.db"
```
And in the bridge:
```python
REPO_BASE = Path.home() / "projects" / "oorep-local-repertory"
```
These hardcoded paths:
1. Leak the system's directory structure (information disclosure in error messages)
2. Make the code brittle (breaks if the project moves)
3. The bridge file exposes the username (`Path.home()` → `/home/walker/...`) in the source code

**Recommended Fix:**
- Use environment variables (`OOREP_DATA_DIR`, `OOREP_DB_PATH`) with sensible defaults
- Use `Path.home() / ".oorep" / "data"` or XDG directories instead of hardcoding project paths
- Never embed `/home/<username>` in source code

---

#### M-03: API Key Stored as Truncated SHA-256 Hash (Weak)
**File:** `oorep/cloud_sync_manager.py` (lines 37-42)  
**Severity:** MEDIUM  
**Description:** The `configure` method stores the API key as a truncated SHA-256 hash:
```python
"api_key_hash": hashlib.sha256(api_key.encode()).hexdigest()[:16] if api_key else None,
```
Issues:
1. Truncating to 16 hex chars (64 bits) significantly weakens collision resistance
2. SHA-256 is fast — vulnerable to brute force if the hash is exposed
3. No salt is used
4. The config file is stored as plaintext JSON (`cloud_sync_config.json`) with no encryption

**Recommended Fix:**
- Use a proper key derivation function (PBKDF2, Argon2) with salt
- Store the full hash, not a truncation
- Encrypt the config file at rest
- Or better: store only a boolean "configured" flag and keep the actual key in a secure vault

---

#### M-04: Race Conditions in SQLite Operations
**Files:** All SQLite-using modules (throughout the codebase)  
**Severity:** MEDIUM  
**Description:** Every database operation follows the pattern:
```python
conn = sqlite3.connect(str(self.db_path))
cursor = conn.cursor()
cursor.execute(...)
conn.commit()
conn.close()
```
Issues:
1. No connection pooling — every operation opens/closes a connection (performance + race condition risk)
2. SQLite's default isolation level is `DEFERRED` — concurrent writers can cause `database is locked` errors
3. No WAL (Write-Ahead Logging) mode enabled — limits concurrent read access
4. The `_previous_hash()` method in `audit_trail.py` (line 103) reads the last hash, then `log()` (line 146) writes a new entry — this is a TOCTOU race: two concurrent `log()` calls can read the same `previous_hash` and break the chain integrity
5. The `_next_version_for_consultation` in `analysis_manager.py` (line 206) has the same TOCTOU issue
6. The `_pseudonym_counter` in `phi_scrubber.py` (line 124) is loaded once and incremented in memory — concurrent instances will produce duplicate pseudonyms

**Recommended Fix:**
- Enable WAL mode: `conn.execute("PRAGMA journal_mode=WAL")`
- Use a connection pool or context manager
- Use explicit transactions with `BEGIN IMMEDIATE` for write operations
- For the hash chain: use a single atomic transaction that reads previous hash and inserts new entry
- For the pseudonym counter: use an auto-increment column or atomic database operation

---

#### M-05: No Rate Limiting on Any API or Portal Endpoint
**Files:** 
- `oorep/mobile_api.py` (all routes)
- `oorep-case-portal/src/app/api/` (all routes)

**Severity:** MEDIUM  
**Description:** No rate limiting is implemented anywhere in the API layer. This allows:
- Brute-force attacks on the admin login (`POST /api/admin/auth`)
- Enumeration of patient pseudonyms via the patient API (`GET /api/patient/{pseudonym}`)
- Abuse of repertorization endpoints (computationally expensive)
- DoS via rapid API calls

**Recommended Fix:**
- Implement rate limiting middleware (e.g., `slowapi` for FastAPI, or Next.js middleware)
- Add per-IP and per-user limits
- Add exponential backoff for failed auth attempts
- Consider CAPTCHA for repeated failures

---

#### M-06: Missing Input Validation in patient_portal.py Token Validation
**File:** `oorep/patient_portal.py` (lines 77-84)  
**Severity:** MEDIUM  
**Description:** The `validate_access_token` method accepts `token` and `case_id` without any validation:
```python
def validate_access_token(self, token: str, case_id: str) -> bool:
    expected = f"portal_{case_id[:8]}"
    return token.startswith(expected)
```
- `case_id` could be empty, None, or contain special characters
- `token` is not validated for length or format before the `startswith` check
- No rate limiting on validation attempts
- The method always returns a bool — timing attacks could be used to enumerate valid token prefixes

**Recommended Fix:**
- Validate both inputs are non-empty strings of expected length
- Use constant-time comparison (`hmac.compare_digest`)
- Add rate limiting on validation attempts
- Log failed validation attempts for security monitoring

---

#### M-07: Prescription PDF Generator Includes Patient Name in Plaintext
**File:** `oorep/prescription_pdf_generator.py` (lines 26-52)  
**Severity:** MEDIUM  
**Description:** The `generate` method accepts `patient_name` as a parameter and embeds it directly in the output:
```python
return {
    ...
    "patient": patient_name,
    ...
    "raw_text": self._format_text(patient_name, ...),
}
```
The `raw_text` field includes `f"Patient: {patient}""` (line 67) in plaintext. If this output is stored or transmitted without encryption, the patient's real name (PHI) is exposed. The module does not use the PHI scrubber or pseudonymization.

**Recommended Fix:**
- Use patient pseudonym instead of real name in generated documents
- Apply PHI scrubbing before storing/transmitting
- Encrypt the output at rest
- Consider redacting patient name in draft versions

---

#### M-08: Social Community JSON File Store Without Access Control
**File:** `oorep/social_community.py` (lines 27-35)  
**Severity:** MEDIUM  
**Description:** The `SocialCommunity` class stores all community posts (including `anonymized_case` data) in a plaintext JSON file:
```python
with open(self.posts_path, "w", encoding="utf-8") as f:
    json.dump(self.posts, f, indent=2)
```
Issues:
1. No file locking — concurrent writes can corrupt the file (race condition)
2. No access control on who can create posts or reply
3. The `anonymize_case` method (line 84) only strips known fields — any extra PHI in `case_data` is silently dropped, but there's no validation that the input doesn't contain additional identifiable information
4. No moderation queue — posts are immediately "published" (line 51)
5. No audit trail for community actions

**Recommended Fix:**
- Use SQLite instead of JSON file for atomic writes
- Add authentication and authorization for posting
- Implement a moderation queue before publishing
- Validate that anonymized case data contains no residual PHI
- Add file locking or use database transactions

---

### LOW

#### L-01: No WAL Mode Enabled on Any SQLite Database
**Files:** All SQLite-using modules  
**Severity:** LOW  
**Description:** No database enables WAL (Write-Ahead Logging) mode. WAL improves concurrent read performance and reduces lock contention. Without WAL, SQLite uses rollback journal mode, which locks the entire database during writes.

**Recommended Fix:** Add `PRAGMA journal_mode=WAL` during database initialization.

---

#### L-02: Audit Trail Verification Available Without Authentication
**File:** `oorep/audit_trail.py` (lines 208-271)  
**Severity:** LOW  
**Description:** The `verify_chain()` method is publicly callable with no authentication. While this is likely intentional (any auditor should be able to verify), the method returns detailed information about the audit log including entry counts and specific broken entry IDs. An attacker could use this to determine if tampering has been detected.

**Recommended Fix:** Consider requiring admin authentication for `verify_chain()` and logging all verification attempts.

---

#### L-03: PHI Scrubber Reversible Mapping Store Unencrypted
**File:** `oorep/phi_scrubber.py` (lines 126-141)  
**Severity:** LOW  
**Description:** When `reversible=True`, the PHI scrubber stores pseudonym-to-real-value mappings in the `phi_mappings` SQLite table in plaintext. This table is the key to reversing pseudonymization — if exposed, all "anonymized" data can be deanonymized. The table stores real names, phone numbers, SSNs, addresses, and dates in cleartext.

**Recommended Fix:**
- Encrypt the `real_value` column using application-layer encryption
- Restrict access to the mapping table (separate database, access controls)
- Consider whether reversible mode is necessary — if so, protect the reversal key separately

---

#### L-04: GitHub Backup Pushes Without Branch Protection Check
**File:** `oorep/cron_tasks.py` (lines 96-142)  
**Severity:** LOW  
**Description:** The `github_backup` method pushes to `origin main` directly:
```python
subprocess.run(["git", "-C", git_dir, "push", "origin", "main"], check=True, ...)
```
This pushes the backup (including SQLite databases with PHI) directly to the main branch. If the GitHub repository is public or has broad collaborator access, this exposes all patient data. The backup also includes `data/` directory which contains `feedback.db` with all PHI.

**Recommended Fix:**
- Push to a private repository only
- Verify repository visibility before pushing
- Exclude database files from git (add to `.gitignore`)
- Use encrypted backups instead of raw SQLite files
- Consider using GitHub Actions secrets for encryption keys

---

#### L-05: Insufficient Input Validation in oorep_bridge.py
**File:** `skills/oorep-hermes-bridge/scripts/oorep_bridge.py` (lines 100-157)  
**Severity:** LOW  
**Description:** The bridge's `handle` method processes natural language input but has no length limits or input sanitization:
- Very long messages could cause performance issues in regex matching
- The fallback repertorize path (line 138) processes arbitrary text as symptoms
- Patient pseudonyms extracted from regex (line 88) are used directly in database queries (though parameterized)

**Recommended Fix:**
- Add maximum message length validation
- Sanitize all extracted groups before use
- Add input length limits for symptom descriptions

---

#### L-06: Billing Integration Lacks Payment Verification
**File:** `oorep/billing_integration.py` (lines 79-87)  
**Severity:** LOW  
**Description:** The `mark_paid` method accepts an `invoice_id` and `method` with no verification that payment actually occurred. There's no integration with a payment processor, no webhook handling, and no signature verification. Any caller can mark any invoice as paid.

**Recommended Fix:**
- Integrate with payment processor webhooks
- Verify payment signatures before marking paid
- Add authentication for billing operations
- Implement payment reconciliation

---

#### L-07: Admin Password Minimum Length Too Low
**File:** `oorep-case-portal/src/app/api/admin/auth/route.ts` (line 9)  
**Severity:** LOW  
**Description:** The admin password minimum length is only 6 characters:
```typescript
if (!password || password.length < 6) {
```
6 characters is insufficient for an administrative account with access to patient data. Modern guidance recommends at least 12 characters.

**Recommended Fix:**
- Increase minimum to 12 characters
- Add complexity requirements (or better, use a passphrase approach)
- Consider using `zxcvbn` for password strength estimation
- Add rate limiting on password attempts

---

## Patterns Not Found (Good Practices)

The following dangerous patterns were **NOT found** in the codebase, indicating good security practices:

1. **No `eval()` or `exec()` calls** — zero instances found in Python source
2. **No `pickle` usage** — all "pickle" matches were in rubric text data (homeopathic symptom descriptions about food pickles), not Python serialization
3. **No `yaml.load()` without safe loader** — zero instances of YAML loading found
4. **No `shell=True` in subprocess calls** — all subprocess calls use argument lists
5. **No hardcoded API keys or passwords** — secrets come from environment variables
6. **Parameterized SQL queries used consistently** — the vast majority of `cursor.execute()` calls use `?` placeholders with tuple parameters
7. **PBKDF2 used for admin password hashing** — the Next.js admin auth uses `crypto.pbkdf2Sync` with 100,000 iterations and SHA-512

---

## Recommendations Summary

### Immediate (Critical Priority)
1. Encrypt all SQLite databases at rest (SQLCipher or filesystem encryption)
2. Add authentication and authorization to the mobile API
3. Replace patient portal token system with cryptographically secure tokens
4. Stop leaking exception details in API error responses

### Short-term (High Priority)
5. Set `secure: true` on admin session cookies
6. Add session expiration to admin portal
7. Fix SQL injection vectors in `outcome_predictor_stats.py` and `patient_cohort_analytics.py`
8. Add path validation in `voice_to_text_audio_import.py`
9. Add input validation to all patient data functions
10. Add rate limiting to all API endpoints

### Medium-term
11. Enable WAL mode on all SQLite databases
12. Fix race conditions in audit trail hash chain and PHI scrubber pseudonym counter
13. Use environment variables instead of hardcoded paths
14. Add moderation queue to social community
15. Encrypt PHI scrubber reversible mappings
16. Improve GitHub backup security (private repo, exclude DBs)
17. Integrate payment verification in billing

### Long-term
18. Implement the encryption described in `cloud_sync_manager.py`
19. Add comprehensive logging and security monitoring
20. Implement proper RBAC across all modules
21. Add automated security testing to CI/CD pipeline