"""
Helper script to set up your SAM.gov API key.
Run this script and paste your API key when prompted.
"""
import os
from pathlib import Path

def setup_env_file():
    """Create or update .env file with API key."""
    env_file = Path(".env")
    
    print("=" * 60)
    print("SAM.gov API Key Setup")
    print("=" * 60)
    print("\nYou can find your API key on SAM.gov Account Details page.")
    print("Click the eye icon to reveal it, or the copy icon to copy it.\n")
    
    # Get API key from user
    api_key = input("Enter your SAM.gov API Key: ").strip()
    
    if not api_key:
        print("\n[ERROR] API key cannot be empty. Exiting.")
        return
    
    # Check if .env already exists
    env_content = ""
    if env_file.exists():
        print(f"\n[INFO] Found existing .env file. Updating it...")
        with open(env_file, 'r') as f:
            env_content = f.read()
    
    # Update or add SAM_API_KEY
    lines = env_content.split('\n') if env_content else []
    updated = False
    new_lines = []
    
    for line in lines:
        if line.startswith('SAM_API_KEY='):
            new_lines.append(f'SAM_API_KEY={api_key}')
            updated = True
        else:
            new_lines.append(line)
    
    if not updated:
        new_lines.append(f'SAM_API_KEY={api_key}')
    
    # Ensure other required configs are present
    required_configs = {
        'SAM_API_BASE_URL': 'https://api.sam.gov/opportunities/v2',
        'DATABASE_URL': 'sqlite:///./samgov_contracts.db',
        'LOG_LEVEL': 'INFO'
    }
    
    for key, default_value in required_configs.items():
        found = any(line.startswith(f'{key}=') for line in new_lines)
        if not found:
            new_lines.append(f'{key}={default_value}')
    
    # Write .env file
    with open(env_file, 'w') as f:
        f.write('\n'.join(new_lines))
        if not new_lines[-1].endswith('\n'):
            f.write('\n')
    
    print(f"\n[OK] API key saved to .env file!")
    print(f"\n[INFO] Your API key expires in 88 days (as shown on SAM.gov)")
    print(f"\n[INFO] To use the API key, restart your Streamlit app:")
    print(f"       streamlit run app.py")
    print("\n" + "=" * 60)

if __name__ == "__main__":
    try:
        setup_env_file()
    except KeyboardInterrupt:
        print("\n\n[INFO] Setup cancelled.")
    except Exception as e:
        print(f"\n[ERROR] An error occurred: {e}")
