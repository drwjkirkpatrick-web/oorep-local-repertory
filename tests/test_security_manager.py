"""
Tests for SecurityManager — comprehensive security module for OOREP

Covers:
1. Input sanitization (SQL injection, path traversal, control chars, length limits)
2. Encryption (round-trip, tamper detection, wrong key rejection)
3. Session management (create, validate, expire, destroy, cleanup)
4. Rate limiting (allow, deny, window reset, per-key isolation)
5. Secure token generation (uniqueness, entropy, format)
6. File integrity monitoring (baseline, detect modification, detect deletion)
7. Error sanitization (path stripping, SQL stripping, length limits)
8. Security event logging
9. Security audit runner
10. Convenience functions
"""

import os
import time
import json
import tempfile
import hashlib
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

import pytest

from oorep.security_manager import (
    SecurityManager,
    SecurityViolation,
    InputValidationError,
    SecurityFinding,
    RateLimitDecision,
    SessionInfo,
    IntegrityReport,
    sanitize,
    secure_token,
    get_security_manager,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def sec(tmp_path):
    """SecurityManager with a temp data directory and database."""
    return SecurityManager(
        data_dir=str(tmp_path / "data"),
        db_path=str(tmp_path / "data" / "security.db"),
    )


@pytest.fixture
def sec_with_data(tmp_path):
    """SecurityManager with a mock data directory containing test DB files."""
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    # Create a mock .db file
    (data_dir / "test.db").write_bytes(b"mock database content")

    # Create a mock oorep module directory
    oorep_dir = tmp_path / "oorep"
    oorep_dir.mkdir(parents=True, exist_ok=True)
    (oorep_dir / "test_module.py").write_text("# safe module\n")

    return SecurityManager(
        data_dir=str(data_dir),
        db_path=str(data_dir / "security.db"),
    ), tmp_path


# ── 1. Input sanitization ─────────────────────────────────────────────────────


class TestInputSanitization:

    def test_strips_null_bytes(self):
        """Null bytes are a classic injection vector."""
        result = SecurityManager.sanitize_input("hello\x00world")
        assert "\x00" not in result
        assert "hello" in result and "world" in result

    def test_strips_control_characters(self):
        """Control characters (except tab and newline) are stripped."""
        result = SecurityManager.sanitize_input("test\x01\x02\x03string")
        assert "\x01" not in result
        assert "\x02" not in result
        assert "\x03" not in result

    def test_preserves_newlines_when_allowed(self):
        result = SecurityManager.sanitize_input("line1\nline2", allow_newlines=True)
        assert "\n" in result

    def test_strips_newlines_when_disallowed(self):
        result = SecurityManager.sanitize_input("line1\nline2", allow_newlines=False)
        assert "\n" not in result
        assert "line1" in result and "line2" in result

    def test_preserves_tabs(self):
        result = SecurityManager.sanitize_input("col1\tcol2")
        assert "\t" in result

    def test_strips_del_character(self):
        result = SecurityManager.sanitize_input("hello\x7fworld")
        assert "\x7f" not in result

    def test_strips_zero_width_spaces(self):
        """Unicode zero-width spaces can bypass regex filters."""
        result = SecurityManager.sanitize_input("hello\u200bworld")
        assert "\u200b" not in result

    def test_strips_bom(self):
        result = SecurityManager.sanitize_input("\ufeffhello")
        assert "\ufeff" not in result

    def test_enforces_max_length(self):
        long_text = "A" * 20_000
        result = SecurityManager.sanitize_input(long_text, max_length=100)
        assert len(result) <= 100

    def test_strips_path_traversal(self):
        """Path traversal sequences are stripped."""
        result = SecurityManager.sanitize_input("../../etc/passwd")
        assert ".." not in result

    def test_strips_url_encoded_path_traversal(self):
        result = SecurityManager.sanitize_input("%2e%2e%2fetc%2fpasswd")
        assert "%2e%2e" not in result.lower()

    def test_handles_none_input(self):
        assert SecurityManager.sanitize_input(None) == ""  # type: ignore

    def test_handles_non_string_input(self):
        result = SecurityManager.sanitize_input(12345)  # type: ignore
        assert isinstance(result, str)
        assert "12345" in result

    def test_strips_whitespace(self):
        result = SecurityManager.sanitize_input("  hello  ")
        assert result == "hello"

    def test_sql_injection_detection(self):
        """SQL injection patterns are detected by check_sql_injection()."""
        is_injection, patterns = SecurityManager.check_sql_injection(
            "'; DROP TABLE users; --"
        )
        assert is_injection is True
        assert len(patterns) > 0

    def test_safe_text_not_flagged_as_sql_injection(self):
        is_injection, patterns = SecurityManager.check_sql_injection(
            "patient has anxiety and restlessness"
        )
        assert is_injection is False


# ── 2. Pseudonym validation ───────────────────────────────────────────────────


class TestPseudonymValidation:

    def test_valid_pseudonym(self):
        assert SecurityManager.validate_pseudonym("MrsJ2024") is True

    def test_valid_with_hyphen(self):
        assert SecurityManager.validate_pseudonym("PT-001") is True

    def test_valid_with_underscore(self):
        assert SecurityManager.validate_pseudonym("patient_001") is True

    def test_rejects_too_short(self):
        assert SecurityManager.validate_pseudonym("AB") is False

    def test_rejects_too_long(self):
        assert SecurityManager.validate_pseudonym("A" * 51) is False

    def test_rejects_special_chars(self):
        assert SecurityManager.validate_pseudonym("patient;drop") is False

    def test_rejects_empty(self):
        assert SecurityManager.validate_pseudonym("") is False

    def test_rejects_none(self):
        assert SecurityManager.validate_pseudonym(None) is False  # type: ignore

    def test_rejects_starts_with_non_alnum(self):
        assert SecurityManager.validate_pseudonym("-patient") is False

    def test_valid_remedy_abbrev(self):
        assert SecurityManager.validate_remedy_abbrev("Ars.") is True
        assert SecurityManager.validate_remedy_abbrev("Nux-v.") is True
        assert SecurityManager.validate_remedy_abbrev("Puls.") is True

    def test_remedy_abbrev_rejects_injection(self):
        assert SecurityManager.validate_remedy_abbrev("Ars'; DROP") is False
        assert SecurityManager.validate_remedy_abbrev("../etc/passwd") is False


# ── 3. Encryption ────────────────────────────────────────────────────────────


class TestEncryption:

    def test_round_trip(self):
        """Encrypt then decrypt returns the original."""
        key, _ = SecurityManager.derive_key("master_password")
        plaintext = "Patient has anxiety with morning headache"
        ciphertext = SecurityManager.encrypt_value(plaintext, key)
        decrypted = SecurityManager.decrypt_value(ciphertext, key)
        assert decrypted == plaintext

    def test_ciphertext_is_not_plaintext(self):
        key, _ = SecurityManager.derive_key("password")
        ciphertext = SecurityManager.encrypt_value("sensitive data", key)
        assert "sensitive" not in ciphertext
        assert "data" not in ciphertext

    def test_different_encryptions_produce_different_ciphertexts(self):
        """Each encryption uses a random nonce — same plaintext → different CT."""
        key, _ = SecurityManager.derive_key("password")
        ct1 = SecurityManager.encrypt_value("same text", key)
        ct2 = SecurityManager.encrypt_value("same text", key)
        assert ct1 != ct2

    def test_wrong_key_fails(self):
        """Decryption with the wrong key raises SecurityViolation."""
        key1, _ = SecurityManager.derive_key("password1")
        key2, _ = SecurityManager.derive_key("password2")
        ciphertext = SecurityManager.encrypt_value("secret", key1)

        with pytest.raises(SecurityViolation):
            SecurityManager.decrypt_value(ciphertext, key2)

    def test_tamper_detection(self):
        """Modifying ciphertext triggers HMAC verification failure."""
        key, _ = SecurityManager.derive_key("password")
        ciphertext = SecurityManager.encrypt_value("original", key)

        # Tamper with the ciphertext
        tampered = ciphertext[:-4] + "0000"

        with pytest.raises(SecurityViolation):
            SecurityManager.decrypt_value(tampered, key)

    def test_associated_data_mismatch_fails(self):
        """Different associated data should cause verification failure."""
        key, _ = SecurityManager.derive_key("password")
        ct = SecurityManager.encrypt_value("data", key, associated_data=b"field1")

        with pytest.raises(SecurityViolation):
            SecurityManager.decrypt_value(ct, key, associated_data=b"field2")

    def test_empty_string_roundtrip(self):
        key, _ = SecurityManager.derive_key("password")
        ct = SecurityManager.encrypt_value("", key)
        assert SecurityManager.decrypt_value(ct, key) == ""

    def test_unicode_roundtrip(self):
        key, _ = SecurityManager.derive_key("password")
        text = "Patient café — naïve résumé"
        ct = SecurityManager.encrypt_value(text, key)
        assert SecurityManager.decrypt_value(ct, key) == text

    def test_derive_key_uses_salt(self):
        """derive_key with the same password but different salts produces different keys."""
        key1, salt1 = SecurityManager.derive_key("password")
        key2, salt2 = SecurityManager.derive_key("password")
        assert salt1 != salt2
        assert key1 != key2

    def test_db_field_encryption_roundtrip(self, sec):
        """Convenience wrapper encrypts and decrypts DB fields."""
        password = "clinic_master_key"
        ct = sec.encrypt_db_field("Sensitive notes", "notes", password)
        pt = sec.decrypt_db_field(ct, "notes", password)
        assert pt == "Sensitive notes"

    def test_db_field_context_separation(self, sec):
        """Same value encrypted for different fields produces different ciphertexts."""
        password = "clinic_master_key"
        ct1 = sec.encrypt_db_field("same value", "field_a", password)
        ct2 = sec.encrypt_db_field("same value", "field_b", password)
        assert ct1 != ct2

    def test_malformed_ciphertext_raises(self):
        key, _ = SecurityManager.derive_key("password")
        with pytest.raises(ValueError):
            SecurityManager.decrypt_value("not_valid_hex!!", key)

    def test_short_ciphertext_raises(self):
        key, _ = SecurityManager.derive_key("password")
        # Only 10 bytes — too short
        short_ct = os.urandom(10).hex()
        with pytest.raises(ValueError):
            SecurityManager.decrypt_value(short_ct, key)


# ── 4. Session management ────────────────────────────────────────────────────


class TestSessionManagement:

    def test_create_session_returns_token(self, sec):
        token = sec.create_session(user_id="dr.walker")
        assert isinstance(token, str)
        assert len(token) == 64  # 32 bytes hex = 64 chars

    def test_validate_valid_session(self, sec):
        token = sec.create_session(user_id="dr.walker")
        assert sec.validate_session(token) is True

    def test_validate_invalid_token(self, sec):
        assert sec.validate_session("invalid_token") is False

    def test_validate_empty_token(self, sec):
        assert sec.validate_session("") is False

    def test_destroy_session(self, sec):
        token = sec.create_session(user_id="dr.walker")
        assert sec.destroy_session(token) is True
        assert sec.validate_session(token) is False

    def test_destroy_nonexistent_session(self, sec):
        assert sec.destroy_session("nonexistent") is False

    def test_session_expires(self, sec):
        """Sessions with very short timeout expire immediately."""
        token = sec.create_session(timeout=timedelta(seconds=0))
        time.sleep(0.1)  # let it expire
        assert sec.validate_session(token) is False

    def test_session_metadata_stored(self, sec):
        token = sec.create_session(
            user_id="dr.walker",
            metadata={"role": "admin", "ip": "10.0.0.1"},
        )
        info = sec.get_session_info(token)
        assert info is not None
        assert info.user_id == "dr.walker"
        assert info.metadata["role"] == "admin"

    def test_cleanup_expired_sessions(self, sec):
        """Expired sessions are removed by cleanup_expired_sessions()."""
        token1 = sec.create_session(timeout=timedelta(seconds=0))
        token2 = sec.create_session(timeout=timedelta(hours=1))

        time.sleep(0.1)
        removed = sec.cleanup_expired_sessions()
        assert removed >= 1
        assert sec.validate_session(token1) is False
        assert sec.validate_session(token2) is True

    def test_session_survives_restart(self, tmp_path):
        """Sessions persisted to DB survive SecurityManager re-initialization."""
        db = str(tmp_path / "data" / "security.db")
        sec1 = SecurityManager(
            data_dir=str(tmp_path / "data"),
            db_path=db,
        )
        token = sec1.create_session(timeout=timedelta(hours=1))

        # Create a new instance — should load from DB
        sec2 = SecurityManager(
            data_dir=str(tmp_path / "data"),
            db_path=db,
        )
        assert sec2.validate_session(token) is True


# ── 5. Rate limiting ──────────────────────────────────────────────────────────


class TestRateLimiting:

    def test_allows_within_limit(self, sec):
        for _ in range(10):
            decision = sec.rate_limit_check("user1", max_requests=10, window_sec=60)
            assert decision.allowed is True

    def test_denies_over_limit(self, sec):
        for _ in range(5):
            sec.rate_limit_check("user2", max_requests=5, window_sec=60)

        decision = sec.rate_limit_check("user2", max_requests=5, window_sec=60)
        assert decision.allowed is False
        assert decision.remaining == 0
        assert decision.retry_after > 0

    def test_per_key_isolation(self, sec):
        """Rate limiting one key doesn't affect another."""
        for _ in range(10):
            sec.rate_limit_check("user_a", max_requests=10, window_sec=60)

        # user_b should still be allowed
        decision = sec.rate_limit_check("user_b", max_requests=10, window_sec=60)
        assert decision.allowed is True

    def test_window_resets(self, sec):
        """After the window passes, the rate limit resets."""
        for _ in range(3):
            sec.rate_limit_check("user3", max_requests=3, window_sec=1)

        # Should be blocked now
        d = sec.rate_limit_check("user3", max_requests=3, window_sec=1)
        assert d.allowed is False

        # Wait for window to reset
        time.sleep(1.1)

        # Should be allowed again
        d = sec.rate_limit_check("user3", max_requests=3, window_sec=1)
        assert d.allowed is True

    def test_remaining_decreases(self, sec):
        for i in range(5):
            d = sec.rate_limit_check("user4", max_requests=5, window_sec=60)
            assert d.allowed is True
            assert d.remaining == 5 - i - 1

    def test_rate_limit_reset(self, sec):
        """Manual reset clears the rate limit for a key."""
        for _ in range(5):
            sec.rate_limit_check("user5", max_requests=5, window_sec=60)
        # Now at limit
        assert sec.rate_limit_check("user5", max_requests=5, window_sec=60).allowed is False

        sec.rate_limit_reset("user5")
        # Should be allowed after reset
        assert sec.rate_limit_check("user5", max_requests=5, window_sec=60).allowed is True


# ── 6. Secure token generation ────────────────────────────────────────────────


class TestSecureTokens:

    def test_portal_token_format(self):
        token = SecurityManager.generate_portal_token("case123")
        assert token.startswith("pt_")
        # "pt_" (3) + 64 hex chars (32 bytes) = 67 total
        assert len(token) == 67

    def test_portal_token_uniqueness(self):
        tokens = [SecurityManager.generate_portal_token("case1") for _ in range(100)]
        assert len(set(tokens)) == 100  # all unique

    def test_api_key_format(self):
        key = SecurityManager.generate_api_key(32)
        assert len(key) == 64  # 32 bytes hex = 64 chars

    def test_api_key_uniqueness(self):
        keys = [SecurityManager.generate_api_key() for _ in range(50)]
        assert len(set(keys)) == 50

    def test_token_hash_is_sha256(self):
        token = "test_token_value"
        h = SecurityManager.hash_token(token)
        assert len(h) == 64  # SHA-256 hex = 64 chars

    def test_verify_token_correct_hash(self):
        token = "my_secret_token"
        h = SecurityManager.hash_token(token)
        assert SecurityManager.verify_token(token, h) is True

    def test_verify_token_wrong_hash(self):
        token = "my_secret_token"
        wrong_hash = "0" * 64
        assert SecurityManager.verify_token(token, wrong_hash) is False

    def test_portal_token_not_predictable(self):
        """Tokens should NOT contain the case_id (unlike old implementation)."""
        case_id = "CASE-12345-XYZ"
        token = SecurityManager.generate_portal_token(case_id)
        assert case_id not in token
        assert case_id[:8] not in token


# ── 7. File integrity monitoring ──────────────────────────────────────────────


class TestFileIntegrity:

    def test_set_baseline(self, tmp_path):
        sec = SecurityManager(
            data_dir=str(tmp_path / "data"),
            db_path=str(tmp_path / "data" / "security.db"),
        )
        test_file = tmp_path / "config.json"
        test_file.write_text('{"version": "1.0"}')
        count = sec.set_integrity_baseline([str(test_file)])
        assert count == 1

    def test_detects_modification(self, tmp_path):
        sec = SecurityManager(
            data_dir=str(tmp_path / "data"),
            db_path=str(tmp_path / "data" / "security.db"),
        )
        test_file = tmp_path / "config.json"
        test_file.write_text('{"version": "1.0"}')
        sec.set_integrity_baseline([str(test_file)])

        # Modify the file
        test_file.write_text('{"version": "2.0"}')

        report = sec.check_file_integrity()
        assert report.failed == 1
        assert report.passed == 0
        assert len(report.changed_files) == 1
        assert report.changed_files[0]["status"] == "modified"

    def test_detects_deletion(self, tmp_path):
        sec = SecurityManager(
            data_dir=str(tmp_path / "data"),
            db_path=str(tmp_path / "data" / "security.db"),
        )
        test_file = tmp_path / "config.json"
        test_file.write_text('{"version": "1.0"}')
        sec.set_integrity_baseline([str(test_file)])

        test_file.unlink()

        report = sec.check_file_integrity()
        assert report.failed == 1
        assert report.changed_files[0]["status"] == "missing"

    def test_passes_when_unchanged(self, tmp_path):
        sec = SecurityManager(
            data_dir=str(tmp_path / "data"),
            db_path=str(tmp_path / "data" / "security.db"),
        )
        test_file = tmp_path / "config.json"
        test_file.write_text('{"version": "1.0"}')
        sec.set_integrity_baseline([str(test_file)])

        report = sec.check_file_integrity()
        assert report.passed == 1
        assert report.failed == 0

    def test_get_monitored_files(self, tmp_path):
        sec = SecurityManager(
            data_dir=str(tmp_path / "data"),
            db_path=str(tmp_path / "data" / "security.db"),
        )
        f1 = tmp_path / "f1.txt"
        f2 = tmp_path / "f2.txt"
        f1.write_text("content1")
        f2.write_text("content2")
        sec.set_integrity_baseline([str(f1), str(f2)])

        files = sec.get_monitored_files()
        assert len(files) == 2

    def test_nonexistent_file_skipped(self, tmp_path):
        sec = SecurityManager(
            data_dir=str(tmp_path / "data"),
            db_path=str(tmp_path / "data" / "security.db"),
        )
        nonexistent = tmp_path / "does_not_exist.txt"
        count = sec.set_integrity_baseline([str(nonexistent)])
        assert count == 0


# ── 8. Error sanitization ─────────────────────────────────────────────────────


class TestErrorSanitization:

    def test_strips_unix_paths(self):
        exc = Exception("Error in /home/walker/projects/oorep/module.py")
        result = SecurityManager.sanitize_error_message(exc)
        assert "/home/walker" not in result
        assert "[PATH]" in result

    def test_strips_db_paths(self):
        exc = Exception("Cannot open data/feedback.db")
        result = SecurityManager.sanitize_error_message(exc)
        assert "feedback.db" not in result

    def test_strips_sql_fragments(self):
        exc = Exception("Error in SELECT * FROM patients WHERE id = 1")
        result = SecurityManager.sanitize_error_message(exc)
        assert "SELECT" not in result
        assert "[SQL]" in result

    def test_strips_line_numbers(self):
        exc = Exception("Error at file.py, line 42, in function")
        result = SecurityManager.sanitize_error_message(exc)
        assert "42" not in result

    def test_safe_error_response_format(self):
        exc = ValueError("Bad input at /home/user/secret/path")
        resp = SecurityManager.safe_error_response(exc, code=400)
        assert resp["status"] == "error"
        assert resp["code"] == 400
        assert "timestamp" in resp
        assert "/home/user" not in resp["error"]

    def test_admin_gets_more_detail(self):
        exc = ValueError("Bad input at /home/user/secret/path")
        user_resp = SecurityManager.safe_error_response(exc, is_admin=False)
        admin_resp = SecurityManager.safe_error_response(exc, is_admin=True)
        # Admin response may be longer (includes_detail)
        assert len(admin_resp["error"]) >= len(user_resp["error"])

    def test_empty_exception_message(self):
        exc = Exception()
        result = SecurityManager.sanitize_error_message(exc)
        assert isinstance(result, str)
        assert len(result) > 0  # falls back to class name


# ── 9. Security event logging ─────────────────────────────────────────────────


class TestSecurityEventLogging:

    def test_log_event(self, sec):
        event_id = sec.log_security_event(
            event_type="test_event",
            severity="info",
            detail="Test event for unit test",
        )
        assert event_id > 0

    def test_retrieve_events(self, sec):
        sec.log_security_event("type1", "info", "detail1")
        sec.log_security_event("type2", "warning", "detail2")

        events = sec.get_security_events(limit=10)
        assert len(events) >= 2
        assert events[0]["event_type"] == "type2"  # newest first

    def test_filter_by_severity(self, sec):
        sec.log_security_event("type1", "info", "detail1")
        sec.log_security_event("type2", "critical", "detail2")

        criticals = sec.get_security_events(severity="critical")
        assert len(criticals) == 1
        assert criticals[0]["severity"] == "critical"

    def test_filter_by_since(self, sec):
        sec.log_security_event("old", "info", "old event")

        # Wait a tiny bit so "since" filters correctly
        # Use local time (same as the log uses datetime.now())
        from datetime import datetime as dt
        cutoff = dt.now().isoformat()
        time.sleep(0.01)
        sec.log_security_event("new", "info", "new event")

        events = sec.get_security_events(since=cutoff)
        # Should only get the "new" event
        assert any(e["event_type"] == "new" for e in events)
        assert not any(e["event_type"] == "old" for e in events)


# ── 10. Security audit runner ─────────────────────────────────────────────────


class TestSecurityAudit:

    def test_audit_returns_findings(self, sec_with_data):
        sec, tmp_path = sec_with_data
        findings = sec.run_security_audit(project_root=str(tmp_path))

        assert isinstance(findings, list)
        # Should find at least the unencrypted .db file
        assert len(findings) > 0

    def test_audit_findings_sorted_by_severity(self, sec_with_data):
        sec, tmp_path = sec_with_data
        findings = sec.run_security_audit(project_root=str(tmp_path))

        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
        for i in range(len(findings) - 1):
            s1 = severity_order.get(findings[i].severity, 99)
            s2 = severity_order.get(findings[i + 1].severity, 99)
            assert s1 <= s2

    def test_audit_report_format(self, sec_with_data):
        sec, tmp_path = sec_with_data
        findings = sec.run_security_audit(project_root=str(tmp_path))
        report = sec.format_audit_report(findings)

        assert "SECURITY AUDIT REPORT" in report
        assert "Total findings" in report

    def test_audit_no_findings(self, tmp_path):
        """Empty project with no DB files produces fewer findings."""
        sec = SecurityManager(
            data_dir=str(tmp_path / "data"),
            db_path=str(tmp_path / "data" / "security.db"),
        )
        # Create an empty project root
        root = tmp_path / "empty_project"
        root.mkdir()
        findings = sec.run_security_audit(project_root=str(root))
        # Should have at least the "no file integrity baseline" finding
        assert isinstance(findings, list)


# ── 11. Convenience functions ─────────────────────────────────────────────────


class TestConvenienceFunctions:

    def test_sanitize_function(self):
        result = sanitize("  hello\x00world  ")
        assert "\x00" not in result
        assert "hello" in result

    def test_secure_token_function(self):
        token = secure_token("case123")
        assert token.startswith("pt_")
        assert "case123" not in token

    def test_get_security_manager_singleton(self):
        mgr = get_security_manager()
        assert isinstance(mgr, SecurityManager)


# ── 12. Integration with existing OOREP modules ──────────────────────────────


class TestOOREPIntegration:

    def test_import_from_oorep_package(self):
        """SecurityManager can be imported from the oorep package."""
        from oorep.security_manager import SecurityManager as SM
        assert SM is SecurityManager

    def test_import_from_oorep_all(self):
        """SecurityManager is exported in oorep.__all__."""
        import oorep
        assert "SecurityManager" in oorep.__all__

    def test_security_manager_works_with_phi_scrubber(self, sec):
        """SecurityManager sanitization is compatible with PHIScrubber."""
        from oorep.phi_scrubber import PHIScrubber

        scrubber = PHIScrubber(reversible=False)
        # Sanitize first, then scrub
        text = "Alice lives at 123 Main St and her SSN is 123-45-6789"
        sanitized = SecurityManager.sanitize_input(text)
        scrubbed = scrubber.scrub(sanitized)
        assert "Alice" not in scrubbed or "[PATIENT]" in scrubbed
        assert "123-45-6789" not in scrubbed

    def test_security_manager_with_audit_trail(self, sec):
        """SecurityManager can verify audit trail integrity."""
        from oorep.audit_trail import AuditTrail

        audit = AuditTrail(db_path=Path(sec.db_path))
        audit.log("test", "test_user", "test/resource", None, {"key": "value"})
        result = audit.verify_chain()
        assert result["intact"] is True