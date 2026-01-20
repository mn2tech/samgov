"""
Quick test script to verify the setup works.
"""
import sys

def test_imports():
    """Test that all imports work."""
    print("Testing imports...")
    try:
        from config import settings
        print("[OK] Config loaded")
        
        from models import Opportunity, CapabilityProfile
        print("[OK] Models imported")
        
        from sam_ingestion import SAMIngestion
        print("[OK] SAM ingestion imported")
        
        from ai_classifier import AIClassifier
        print("[OK] AI classifier imported")
        
        from ai_scoring import AIScoringEngine
        print("[OK] AI scoring imported")
        
        from profile_manager import profile_manager
        print("[OK] Profile manager imported")
        
        from database import db
        print("[OK] Database imported")
        
        print("\n[OK] All imports successful!")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Import error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config():
    """Test configuration."""
    print("\nTesting configuration...")
    try:
        from config import settings
        print(f"[OK] Database URL: {settings.database_url}")
        print(f"[OK] SAM API Key: {'Set' if settings.sam_api_key else 'Not set (will use mock data)'}")
        print(f"[OK] OpenAI API Key: {'Set' if settings.openai_api_key else 'Not set (will use rule-based)'}")
        print(f"[OK] Ollama URL: {settings.ollama_base_url or 'Not set'}")
        return True
    except Exception as e:
        print(f"[ERROR] Config error: {e}")
        return False

def test_database():
    """Test database connection."""
    print("\nTesting database...")
    try:
        from database import db
        session = db.get_session()
        session.close()
        print("[OK] Database connection successful!")
        return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("AI Contract Finder - Setup Test")
    print("=" * 50)
    
    all_passed = True
    all_passed &= test_imports()
    all_passed &= test_config()
    all_passed &= test_database()
    
    print("\n" + "=" * 50)
    if all_passed:
        print("[OK] All tests passed! You're ready to run the app.")
        print("\nTo start the Streamlit UI, run:")
        print("  streamlit run app.py")
    else:
        print("[ERROR] Some tests failed. Please check the errors above.")
    print("=" * 50)
    
    sys.exit(0 if all_passed else 1)
