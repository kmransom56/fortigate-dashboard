#!/usr/bin/env python3
"""
Download TurboSparse models from Hugging Face
"""

import os
import sys
from huggingface_hub import snapshot_download

MODELS_DIR = "/media/keith/DATASTORE/models"
REPO_ID = "SJTU-IPADS/PowerInfer"

def download_model(model_name: str):
    """Download a TurboSparse model"""
    local_dir = os.path.join(MODELS_DIR, model_name)
    
    print(f"Downloading {model_name}...")
    print(f"Destination: {local_dir}")
    print("This may take a while (models are large)...")
    print("")
    
    try:
        # TurboSparse models may be in specific subdirectories
        # Try different repository paths
        repo_paths = [
            f"SJTU-IPADS/{model_name}",
            f"SJTU-IPADS/PowerInfer",
            f"PowerInfer/{model_name}",
        ]
        
        downloaded = False
        for repo_path in repo_paths:
            try:
                print(f"Trying repository: {repo_path}...")
                snapshot_download(
                    repo_id=repo_path,
                    local_dir=local_dir,
                    local_dir_use_symlinks=False
                )
                print(f"✅ Successfully downloaded {model_name} from {repo_path}")
                downloaded = True
                break
            except Exception as e:
                print(f"   Not found at {repo_path}, trying next...")
                continue
        
        if not downloaded:
            # Try listing available files
            from huggingface_hub import list_repo_files
            print(f"\nListing files in {REPO_ID}...")
            try:
                files = list_repo_files(REPO_ID, repo_type="model")
                print("Available files/directories:")
                for f in files[:20]:  # Show first 20
                    print(f"  - {f}")
                print("\nPlease check Hugging Face for the correct model path:")
                print("  https://huggingface.co/SJTU-IPADS/PowerInfer")
            except:
                pass
            
            print(f"\n⚠️  Could not auto-download {model_name}")
            print("   Please download manually from:")
            print("   https://huggingface.co/SJTU-IPADS/PowerInfer")
            return False
        
        print(f"✅ Successfully downloaded {model_name}")
        print(f"   Location: {local_dir}")
        return True
    except Exception as e:
        print(f"❌ Error downloading {model_name}: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("TurboSparse Model Downloader")
    print("=" * 60)
    print("")
    
    # Create models directory
    os.makedirs(MODELS_DIR, exist_ok=True)
    
    # Available models
    models = {
        "1": ("TurboSparse-Mistral-7B", "7B parameter model (~14GB)"),
        "2": ("TurboSparse-Mixtral-47B", "47B parameter model (~28GB)"),
        "3": ("Both", "Download both models")
    }
    
    print("Available models:")
    for key, (name, desc) in models.items():
        print(f"  {key}. {name} - {desc}")
    print("")
    
    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        choice = input("Select model to download (1-3): ").strip()
    
    if choice == "1":
        download_model("TurboSparse-Mistral-7B")
    elif choice == "2":
        download_model("TurboSparse-Mixtral-47B")
    elif choice == "3":
        download_model("TurboSparse-Mistral-7B")
        print("")
        download_model("TurboSparse-Mixtral-47B")
    else:
        print("Invalid choice")
        sys.exit(1)
    
    print("")
    print("=" * 60)
    print("Download Complete!")
    print("=" * 60)
    print("")
    print("Next steps:")
    print("  1. Test PowerInfer with the model")
    print("  2. Update configuration to use the model")
    print("  3. Run: python3 meraki_tui.py")

if __name__ == "__main__":
    main()
