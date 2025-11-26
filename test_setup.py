"""
Quick setup verification script
Run this to verify your environment is configured correctly
"""
import sys
from pathlib import Path

def test_imports():
    """Test that all required packages are installed"""
    print("Testing imports...")
    try:
        import streamlit
        import supabase
        import google.generativeai
        import PyPDF2
        from docx import Document
        from pptx import Presentation
        from PIL import Image
        import tiktoken
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Run: pip install -r requirements.txt")
        return False

def test_config():
    """Test configuration loading"""
    print("\nTesting configuration...")
    try:
        from config import Config
        Config.validate()
        print("✅ Configuration loaded successfully")
        return True
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("Check your .env file")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_supabase_connection():
    """Test Supabase connection"""
    print("\nTesting Supabase connection...")
    try:
        from src.database.supabase_client import SupabaseClient
        client = SupabaseClient()
        print("✅ Supabase connection successful")
        return True
    except Exception as e:
        print(f"❌ Supabase connection error: {e}")
        print("Check your Supabase URL and keys in .env")
        return False

def test_embedding_service():
    """Test embedding service"""
    print("\nTesting embedding service...")
    try:
        from src.embeddings.embedding_service import EmbeddingService
        service = EmbeddingService()
        # Test with a small text
        test_text = "This is a test sentence for embedding."
        embedding = service.generate_embedding(test_text)
        print(f"✅ Embedding generated successfully (dimension: {len(embedding)})")
        print(f"   Note: Update VECTOR_DIMENSION in config.py if this differs from 768")
        return True
    except Exception as e:
        print(f"❌ Embedding service error: {e}")
        print("Check your Google API key in .env")
        return False

def main():
    """Run all tests"""
    print("=" * 50)
    print("Spotlight Academy - Setup Verification")
    print("=" * 50)
    
    results = []
    results.append(("Imports", test_imports()))
    results.append(("Configuration", test_config()))
    results.append(("Supabase", test_supabase_connection()))
    results.append(("Embedding Service", test_embedding_service()))
    
    print("\n" + "=" * 50)
    print("Summary:")
    print("=" * 50)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All tests passed! You're ready to use the application.")
        print("Run: streamlit run app.py")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()

