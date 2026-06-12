"""tests/test_anonymizer.py — Unit tests for anonymization service."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.anonymizer import anonymize, anonymize_report


def test_email_anonymized():
    result = anonymize("Contact john.doe@acme.com for help.")
    assert "[EMAIL]" in result
    assert "john.doe@acme.com" not in result


def test_ip_anonymized():
    result = anonymize("Server at 192.168.1.100 is down.")
    assert "[IP_ADDRESS]" in result
    assert "192.168.1.100" not in result


def test_ticket_id_anonymized():
    for ticket in ["INC-1234", "TKT-5678", "REQ-999", "CHG-42"]:
        result = anonymize(f"Resolved {ticket}.")
        assert "[TICKET_ID]" in result, f"{ticket} not anonymized"


def test_host_anonymized():
    result = anonymize("Restarted srv-db-02 and host-app-07.")
    assert "[HOST]" in result


def test_password_redacted():
    result = anonymize("Set password=MySecret123 in config.")
    assert "MySecret123" not in result
    assert "[REDACTED]" in result


def test_clean_text_unchanged():
    clean = "The database connection pool was exhausted during peak hours."
    result = anonymize(clean)
    assert result == clean


def test_anonymize_report():
    text = "INC-100 user john@corp.com on 10.0.0.1"
    report = anonymize_report(text, anonymize(text))
    assert "Emails" in report or "IPs" in report or "Ticket IDs" in report


if __name__ == "__main__":
    tests = [
        test_email_anonymized,
        test_ip_anonymized,
        test_ticket_id_anonymized,
        test_host_anonymized,
        test_password_redacted,
        test_clean_text_unchanged,
        test_anonymize_report,
    ]
    passed = failed = 0
    for t in tests:
        try:
            t()
            print(f"  ✅ PASS  {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  ❌ FAIL  {t.__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
