"""
Quick verification script for Digital Human Coach PoC
Run this to verify your setup is working
"""
import sys
from pathlib import Path
import importlib.util

def check_dependencies():
    """Check if required packages are installed"""
    print("\n📦 Checking dependencies...")
    required = {
        'fastapi': 'FastAPI',
        'uvicorn': 'Uvicorn',
        'requests': 'Requests',
        'loguru': 'Loguru',
        'streamlit': 'Streamlit',
        'pydantic': 'Pydantic'
    }
    missing = []
    
    for package, name in required.items():
        spec = importlib.util.find_spec(package)
        if spec is not None:
            print(f"  ✅ {name}")
        else:
            print(f"  ❌ {name} - NOT INSTALLED")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️ Missing packages: {', '.join(missing)}")
        print("Run: pip install -r requirements.txt")
        return False
    return True

def check_file_structure():
    """Verify project structure"""
    print("\n📁 Checking file structure...")
    required_files = [
        "app/backend/main.py",
        "app/backend/api/conversation.py",
        "app/backend/api/evaluation.py",
        "app/backend/models/schemas.py",
        "app/backend/services/stt_service.py",
        "app/backend/services/llm_service.py",
        "app/backend/services/tts_service.py",
        "app/backend/services/pose_service.py",
        "app/backend/services/metrics_service.py",
        "app/utils/storage.py",
        "app/frontend/main.py"
    ]
    
    all_exist = True
    for file_path in required_files:
        path = Path(file_path)
        if path.exists():
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} - NOT FOUND")
            all_exist = False
    
    return all_exist

def test_imports():
    """Test if modules can be imported"""
    print("\n🔧 Testing module imports...")
    
    modules = [
        ("app.backend.models.schemas", "Schemas"),
        ("app.utils.storage", "Storage Service"),
        ("app.backend.services.llm_service", "LLM Service"),
        ("app.backend.services.stt_service", "STT Service"),
        ("app.backend.services.tts_service", "TTS Service"),
        ("app.backend.services.pose_service", "Pose Service"),
        ("app.backend.services.metrics_service", "Metrics Service"),
    ]
    
    all_ok = True
    for module_name, display_name in modules:
        try:
            __import__(module_name)
            print(f"  ✅ {display_name}")
        except ImportError as e:
            print(f"  ❌ {display_name} - Import Error: {str(e)[:50]}")
            all_ok = False
        except Exception as e:
            print(f"  ⚠️ {display_name} - Error: {str(e)[:50]}")
    
    return all_ok

def test_backend_connection():
    """Test if backend server is running"""
    print("\n🚀 Testing backend server connection...")
    print("Checking http://localhost:8000")
    
    try:
        import requests
        response = requests.get("http://localhost:8000/health", timeout=2)
        if response.status_code == 200:
            print("  ✅ Backend is running!")
            data = response.json()
            print(f"  Status: {data.get('status')}")
            return True
    except ImportError:
        print("  ⚠️ Requests library not available")
        return False
    except Exception as e:
        print("  ⚠️ Backend is not running")
        print(f"  Error: {str(e)}")
        return False

def main():
    """Main verification flow"""
    print("=" * 60)
    print("DIGITAL HUMAN COACH - QUICK VERIFICATION")
    print("=" * 60)
    
    results = {}
    
    # Step 1: Check dependencies
    results['dependencies'] = check_dependencies()
    
    # Step 2: Check file structure
    results['files'] = check_file_structure()
    
    # Step 3: Test imports
    results['imports'] = test_imports()
    
    # Step 4: Test backend
    results['backend'] = test_backend_connection()
    
    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    for check, status in results.items():
        status_icon = "✅" if status else "⚠️"
        print(f"{status_icon} {check.capitalize()}: {'PASSED' if status else 'NEEDS ATTENTION'}")
    
    print("\n" + "=" * 60)
    
    if results['backend']:
        print("✅ System is ready for testing!")
        print("\n📚 Next steps:")
        print("  1. Run integration tests: python test_integration.py")
        print("  2. Start frontend: streamlit run app/frontend/main.py")
        print("  3. Access API docs: http://localhost:8000/docs")
    else:
        print("⚠️ Backend needs to be started")
        print("\n🚀 To start the system:")
        print("  Terminal 1: python -m app.backend.main")
        print("  Terminal 2: streamlit run app/frontend/main.py")
        print("  Then run this script again to verify")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
