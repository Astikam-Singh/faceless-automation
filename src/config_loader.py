import os
import yaml

def get_config_path():
    """Returns the absolute path to config.yaml regardless of execution directory."""
    # Try looking in the current working directory first (often the repo root in Ci/CD)
    cwd_path = os.path.join(os.getcwd(), 'config.yaml')
    if os.path.exists(cwd_path):
        return cwd_path
        
    # Fallback to relative calculation
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, 'config.yaml')
    
    # Debug print for CI/CD visibility
    print(f"DEBUG: Looking for config at: {config_path}")
    print(f"DEBUG: Root dir exists: {os.path.exists(base_dir)}")
    print(f"DEBUG: Config exists: {os.path.exists(config_path)}")
    print(f"DEBUG: Current directory contents: {os.listdir(os.getcwd())}")
    
    return config_path

def load_config():
    """Loads the configuration from config.yaml."""
    config_path = get_config_path()
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.load(f, Loader=yaml.SafeLoader)
