"""
Script to list available NVIDIA API models
"""
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def list_nvidia_models():
    """List all available NVIDIA API models"""
    api_key = os.getenv("NVIDIA_API_KEY")
    
    if not api_key or api_key == "your_nvidia_api_key_here":
        print("❌ NVIDIA_API_KEY not set or using placeholder value")
        print("\nTo use NVIDIA API:")
        print("1. Get an API key from https://build.nvidia.com/")
        print("2. Update NVIDIA_API_KEY in .env file")
        return
    
    print("🔍 Fetching available NVIDIA models...\n")
    
    try:
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        response = requests.get(
            "https://integrate.api.nvidia.com/v1/models",
            headers=headers
        )
        
        if response.status_code == 200:
            models = response.json()
            
            if isinstance(models, dict) and "data" in models:
                models = models["data"]
            
            print(f"✅ Found {len(models)} available models:\n")
            
            # Categorize models
            chat_models = []
            embedding_models = []
            other_models = []
            
            for model in models:
                model_id = model.get("id", "unknown")
                
                # Categorize based on model name patterns
                if any(x in model_id.lower() for x in ["llama", "qwen", "mistral", "mixtral", "chat", "instruct"]):
                    chat_models.append(model_id)
                elif "embed" in model_id.lower():
                    embedding_models.append(model_id)
                else:
                    other_models.append(model_id)
            
            # Print chat/instruct models
            if chat_models:
                print("💬 Chat/Instruction Models:")
                for model in sorted(chat_models):
                    print(f"   • {model}")
                print()
            
            # Print embedding models
            if embedding_models:
                print("🔢 Embedding Models:")
                for model in sorted(embedding_models):
                    print(f"   • {model}")
                print()
            
            # Print other models
            if other_models:
                print("🔧 Other Models:")
                for model in sorted(other_models):
                    print(f"   • {model}")
                print()
            
            print("\n📝 Recommended chat models for conversation:")
            recommended = [
                "qwen/qwen3-next-80b-a3b-instruct",
                "meta/llama-3.1-405b-instruct",
                "mistralai/mixtral-8x7b-instruct-v0.1",
            ]
            for model in recommended:
                if model in chat_models:
                    print(f"   ✓ {model}")
                else:
                    print(f"   ? {model} (might be available)")
            
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error fetching models: {e}")


if __name__ == "__main__":
    list_nvidia_models()
