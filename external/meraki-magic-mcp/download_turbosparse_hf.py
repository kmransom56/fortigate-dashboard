#!/usr/bin/env python3
"""
Download TurboSparse models from Hugging Face
"""

import os
import sys
from huggingface_hub import snapshot_download, HfApi, list_repo_files
import json

MODELS_DIR = "/media/keith/DATASTORE/models"

def find_turbosparse_models():
    """Find TurboSparse model repositories"""
    print("Searching for TurboSparse models on Hugging Face...")
    print("")
    
    api = HfApi()
    
    # Search for TurboSparse models
    print("1. Searching for 'turbosparse' models...")
    turbosparse_models = list(api.list_models(search='turbosparse', limit=50))
    print(f"   Found {len(turbosparse_models)} models")
    
    # Search in SJTU-IPADS organization
    print("\n2. Searching SJTU-IPADS organization...")
    sjtu_models = list(api.list_models(author='SJTU-IPADS', limit=100))
    print(f"   Found {len(sjtu_models)} models")
    
    # Filter for TurboSparse
    relevant = []
    for model in sjtu_models:
        if any(term in model.id.lower() for term in ['turbosparse', 'turbo', 'mistral', 'mixtral', 'powerinfer']):
            relevant.append(model)
    
    print(f"   Found {len(relevant)} relevant models")
    print("")
    
    # Display found models
    print("=" * 60)
    print("Available TurboSparse Models:")
    print("=" * 60)
    
    mistral_models = [m for m in relevant if 'mistral' in m.id.lower() and '7b' in m.id.lower()]
    mixtral_models = [m for m in relevant if 'mixtral' in m.id.lower() and '47b' in m.id.lower()]
    
    if mistral_models:
        print("\nTurboSparse-Mistral-7B candidates:")
        for m in mistral_models[:5]:
            print(f"  - {m.id}")
    
    if mixtral_models:
        print("\nTurboSparse-Mixtral-47B candidates:")
        for m in mixtral_models[:5]:
            print(f"  - {m.id}")
    
    # Also check PowerInfer repos
    powerinfer_models = [m for m in relevant if 'powerinfer' in m.id.lower()]
    if powerinfer_models:
        print("\nPowerInfer model repositories:")
        for m in powerinfer_models[:5]:
            print(f"  - {m.id}")
    
    print("")
    return relevant

def download_model(repo_id: str, model_name: str):
    """Download a model from Hugging Face"""
    local_dir = os.path.join(MODELS_DIR, model_name)
    
    print(f"\n{'='*60}")
    print(f"Downloading: {model_name}")
    print(f"Repository: {repo_id}")
    print(f"Destination: {local_dir}")
    print(f"{'='*60}")
    print("")
    
    # Check if already exists
    if os.path.exists(local_dir) and os.listdir(local_dir):
        print(f"⚠️  Directory already exists: {local_dir}")
        response = input("Continue anyway? (y/n): ").strip().lower()
        if response != 'y':
            print("Skipping...")
            return False
    
    try:
        print("Starting download (this may take a while)...")
        print("")
        
        # Download with progress
        snapshot_download(
            repo_id=repo_id,
            local_dir=local_dir,
            local_dir_use_symlinks=False,
            resume_download=True
        )
        
        print("")
        print(f"✅ Successfully downloaded {model_name}")
        print(f"   Location: {local_dir}")
        
        # List downloaded files
        files = os.listdir(local_dir)
        print(f"   Files: {len(files)}")
        for f in files[:10]:
            size = os.path.getsize(os.path.join(local_dir, f)) / (1024*1024)
            print(f"     - {f} ({size:.1f} MB)")
        if len(files) > 10:
            print(f"     ... and {len(files) - 10} more files")
        
        return True
        
    except Exception as e:
        print(f"❌ Error downloading {model_name}: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("TurboSparse Model Downloader (Hugging Face)")
    print("=" * 60)
    print("")
    
    # Create models directory
    os.makedirs(MODELS_DIR, exist_ok=True)
    print(f"Models directory: {MODELS_DIR}")
    print("")
    
    # Find models
    models = find_turbosparse_models()
    
    if not models:
        print("⚠️  No TurboSparse models found automatically")
        print("")
        print("Please provide repository ID manually:")
        print("  Example: SJTU-IPADS/TurboSparse-Mistral-7B")
        print("")
        repo_id = input("Repository ID: ").strip()
        if repo_id:
            model_name = repo_id.split('/')[-1]
            download_model(repo_id, model_name)
        return
    
    # Common model names to try
    common_models = {
        "TurboSparse-Mistral-7B": [
            "SJTU-IPADS/TurboSparse-Mistral-7B",
            "SJTU-IPADS/PowerInfer-TurboSparse-Mistral-7B",
            "PowerInfer/TurboSparse-Mistral-7B",
        ],
        "TurboSparse-Mixtral-47B": [
            "SJTU-IPADS/TurboSparse-Mixtral-47B",
            "SJTU-IPADS/PowerInfer-TurboSparse-Mixtral-47B",
            "PowerInfer/TurboSparse-Mixtral-47B",
        ]
    }
    
    print("")
    print("Select model to download:")
    print("  1. TurboSparse-Mistral-7B")
    print("  2. TurboSparse-Mixtral-47B")
    print("  3. Both")
    print("  4. Enter custom repository ID")
    print("")
    
    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        choice = input("Choice (1-4): ").strip()
    
    if choice == "1":
        # Try to find Mistral model
        for repo_id in common_models["TurboSparse-Mistral-7B"]:
            try:
                # Check if repo exists
                files = list(list_repo_files(repo_id, repo_type="model"))
                if files:
                    download_model(repo_id, "TurboSparse-Mistral-7B")
                    break
            except:
                continue
        else:
            print("⚠️  Could not find TurboSparse-Mistral-7B automatically")
            print("   Please check Hugging Face manually: https://huggingface.co/SJTU-IPADS")
    
    elif choice == "2":
        # Try to find Mixtral model
        for repo_id in common_models["TurboSparse-Mixtral-47B"]:
            try:
                files = list(list_repo_files(repo_id, repo_type="model"))
                if files:
                    download_model(repo_id, "TurboSparse-Mixtral-47B")
                    break
            except:
                continue
        else:
            print("⚠️  Could not find TurboSparse-Mixtral-47B automatically")
            print("   Please check Hugging Face manually: https://huggingface.co/SJTU-IPADS")
    
    elif choice == "3":
        # Download both
        for model_name, repo_ids in common_models.items():
            downloaded = False
            for repo_id in repo_ids:
                try:
                    files = list(list_repo_files(repo_id, repo_type="model"))
                    if files:
                        download_model(repo_id, model_name)
                        downloaded = True
                        break
                except:
                    continue
            if not downloaded:
                print(f"⚠️  Could not find {model_name}")
    
    elif choice == "4":
        repo_id = input("Repository ID (e.g., SJTU-IPADS/ModelName): ").strip()
        if repo_id:
            model_name = repo_id.split('/')[-1]
            download_model(repo_id, model_name)
    
    print("")
    print("=" * 60)
    print("Download Complete!")
    print("=" * 60)
    print("")
    print("Next steps:")
    print("  1. Verify models: ls -lh /media/keith/DATASTORE/models/")
    print("  2. Test PowerInfer: python3 test_powerinfer_speedup.py")
    print("  3. Use in TUI: python3 meraki_tui.py")

if __name__ == "__main__":
    main()
