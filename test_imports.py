"""
Test script to verify all imports work correctly.
Run this to diagnose import issues.
"""
import sys

print("Testing imports...")
print(f"Python version: {sys.version}")
print()

try:
    print("1. Testing config...")
    from config import settings
    print("   ✓ config imported")
except Exception as e:
    print(f"   ✗ config failed: {e}")
    sys.exit(1)

try:
    print("2. Testing database...")
    from database import db
    print("   ✓ database imported")
    # Test database connection
    session = db.get_session()
    session.close()
    print("   ✓ database connection works")
except Exception as e:
    print(f"   ✗ database failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    print("3. Testing models...")
    from models import Opportunity, CapabilityProfile, OpportunityScore
    print("   ✓ models imported")
except Exception as e:
    print(f"   ✗ models failed: {e}")
    sys.exit(1)

try:
    print("4. Testing auth...")
    from auth import check_authentication
    print("   ✓ auth imported")
except Exception as e:
    print(f"   ✗ auth failed: {e}")
    sys.exit(1)

try:
    print("5. Testing profile_manager...")
    from profile_manager import profile_manager
    print("   ✓ profile_manager imported")
except Exception as e:
    print(f"   ✗ profile_manager failed: {e}")
    sys.exit(1)

try:
    print("6. Testing sam_ingestion...")
    from sam_ingestion import SAMIngestion
    print("   ✓ sam_ingestion imported")
except Exception as e:
    print(f"   ✗ sam_ingestion failed: {e}")
    sys.exit(1)

try:
    print("7. Testing ai_classifier...")
    from ai_classifier import AIClassifier
    print("   ✓ ai_classifier imported")
except Exception as e:
    print(f"   ✗ ai_classifier failed: {e}")
    sys.exit(1)

try:
    print("8. Testing ai_scoring...")
    from ai_scoring import AIScoringEngine
    print("   ✓ ai_scoring imported")
except Exception as e:
    print(f"   ✗ ai_scoring failed: {e}")
    sys.exit(1)

try:
    print("9. Testing ai_bid_assistant...")
    from ai_bid_assistant import bid_assistant
    print("   ✓ ai_bid_assistant imported")
except Exception as e:
    print(f"   ✗ ai_bid_assistant failed: {e}")
    sys.exit(1)

try:
    print("10. Testing streamlit...")
    import streamlit as st
    print("   ✓ streamlit imported")
except Exception as e:
    print(f"   ✗ streamlit failed: {e}")
    sys.exit(1)

print()
print("=" * 50)
print("✓ All imports successful!")
print("=" * 50)
