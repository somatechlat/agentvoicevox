import os
import sys

# Add the backend directory to the Python path.
sys.path.insert(0, os.path.abspath('../../ovos-voice-agent/AgentVoiceBoxEngine/backend'))

# Set the Django settings module.
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.testing'
os.environ["TESTING"] = "true"

try:
    import django
    django.setup()
    from django.conf import settings
    print(f"Django settings module: {os.environ['DJANGO_SETTINGS_MODULE']}")
    print(f"Django DEBUG setting: {settings.DEBUG}")
    print("Django settings imported successfully!")
except Exception as e:
    print(f"Error importing Django settings: {e}")
    sys.exit(1)
