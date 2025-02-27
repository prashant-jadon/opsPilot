import os
from dotenv import load_dotenv

def load_config():
    load_dotenv()
    
    required_vars = ['GEMINI_API_KEY', 'MONGODB_URI']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing_vars)}\n"
            "Please check your .env file."
        )
    
    return {
        'gemini_api_key': os.getenv('GEMINI_API_KEY'),
        'mongodb_uri': os.getenv('MONGODB_URI')
    }

# Add a central theme configuration
class ThemeConfig:
    # Primary colors
    PRIMARY = "#2563EB"      # Bright Blue
    SECONDARY = "#8B5CF6"    # Purple
    SUCCESS = "#10B981"      # Emerald
    WARNING = "#F59E0B"      # Amber
    DANGER = "#EF4444"      # Red
    INFO = "#3B82F6"        # Blue
    
    # Background colors
    BG_PRIMARY = "#F0F9FF"   # Light Blue
    BG_SECONDARY = "#F5F3FF" # Light Purple
    BG_SUCCESS = "#ECFDF5"   # Light Green
    BG_WARNING = "#FFFBEB"   # Light Amber
    BG_DANGER = "#FEE2E2"    # Light Red
    
    # Text colors
    TEXT_PRIMARY = "#1F2937"   # Dark Gray
    TEXT_SECONDARY = "#4B5563" # Medium Gray
    TEXT_LIGHT = "#6B7280"     # Light Gray
    
    # Status colors
    STATUS_COLORS = {
        'pending': WARNING,
        'in_progress': PRIMARY,
        'completed': SUCCESS,
        'overdue': DANGER
    }
    
    # Card styles
    CARD_STYLE = """
        background-color: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        border: 1px solid rgba(0,0,0,0.05);
    """
    
    # Button styles
    BUTTON_STYLE = """
        background-color: {color};
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 6px;
        font-weight: 500;
        transition: all 0.2s;
    """ 