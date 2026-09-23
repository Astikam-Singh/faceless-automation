import os
import yaml

def get_config_path():
    """Returns the absolute path to config.yaml (or config.template.yaml)"""
    # 1. Look for config.yaml (if user provided it locally)
    config_yaml = os.path.join(os.getcwd(), 'config.yaml')
    if os.path.exists(config_yaml):
        return config_yaml
        
    # 2. Fallback to config.template.yaml (for CI/CD environments)
    template_yaml = os.path.join(os.getcwd(), 'config.template.yaml')
    if os.path.exists(template_yaml):
        return template_yaml
        
    raise FileNotFoundError("Neither config.yaml nor config.template.yaml found!")

def load_config():
    """Loads the configuration with support for environment variable overrides."""
    path = get_config_path()
    with open(path, "r", encoding="utf-8") as f:
        config = yaml.load(f, Loader=yaml.SafeLoader)
        
    # Override with env vars if present (Crucial for CI/CD)
    if os.getenv("GOOGLE_GEMINI_API_KEY"): config['google_gemini_api_key'] = os.getenv("GOOGLE_GEMINI_API_KEY")
    if os.getenv("PEXELS_API_KEY"): config['pexels_api_key'] = os.getenv("PEXELS_API_KEY")
    if os.getenv("PIXABAY_API_KEY"): config['pixabay_api_key'] = os.getenv("PIXABAY_API_KEY")
    if os.getenv("HUGGINGFACE_API_KEY"): config['tts']['huggingface_api_key'] = os.getenv("HUGGINGFACE_API_KEY")
    
    return config
