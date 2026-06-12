"""tests/test_pdf_generator.py — Unit tests for PDF generation."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

SAMPLE_MD = """# Database Timeout Resolution

**Category:** Database
**Severity:** High
**Tags:** database, timeout, performance

## Summary
Connection pool was exhausted during peak load causing application freezes.

## Symptoms
- Application UI freezing for users
- Database connection timeout errors in logs

## Root Cause
A long-running report query held connections for 8+ minutes, exhausting the pool.

## Resolution Steps
1. Identified blocking query using `pg_stat_activity`
2. Killed the query with `SELECT pg_terminate_backend(pid)`
3. Increased connection pool max from 50 to 100

## Validation Steps
Monitor connection pool metrics for 30 minutes after fix.

## Preventive Measures
- Set query timeout to 60 seconds
- Add index on high-cardinality join columns

## References
- N/A
"""


def test_pdf_returns_bytes():
    from services.pdf_generator import create_kb_pdf
    result = create_kb_pdf(SAMPLE_MD, title="Test Article", review_status="New")
    assert isinstance(result, bytes)


def test_pdf_has_valid_header():
    from services.pdf_generator import create_kb_pdf
    result = create_kb_pdf(SAMPLE_MD)
    # All valid PDFs start with %PDF-
    assert result[:5] == b"%PDF-", f"Expected PDF header, got: {result[:10]}"


def test_pdf_minimum_size():
    from services.pdf_generator import create_kb_pdf
    result = create_kb_pdf(SAMPLE_MD)
    # A real PDF with content should be > 2KB
    assert len(result) > 2048, f"PDF too small: {len(result)} bytes"


def test_pdf_with_code_blocks():
    md = SAMPLE_MD + "\n```bash\nkill -9 1234\nsystemctl restart app\n```\n"
    from services.pdf_generator import create_kb_pdf
    result = create_kb_pdf(md)
    assert result[:5] == b"%PDF-"


def test_pdf_with_custom_status():
    from services.pdf_generator import create_kb_pdf
    result = create_kb_pdf(SAMPLE_MD, title="Custom Title", review_status="Approved")
    assert isinstance(result, bytes)
    assert len(result) > 2048


if __name__ == "__main__":
    tests = [
        test_pdf_returns_bytes,
        test_pdf_has_valid_header,
        test_pdf_minimum_size,
        test_pdf_with_code_blocks,
        test_pdf_with_custom_status,
    ]
    passed = failed = 0
    for t in tests:
        try:
            t()
            print(f"  ✅ PASS  {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"  ❌ FAIL  {t.__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
