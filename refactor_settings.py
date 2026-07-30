import os
import re

settings_path = r'c:\Users\atika\Documents\hridoy\my-project_new_eddition\sports-go\pobon_maker_backend\pobon_maker_backend\settings.py'
with open(settings_path, 'r') as f:
    content = f.read()

# 1. Add environ import and initialization at the top
import_block = """from pathlib import Path
import environ
import os

env = environ.Env(
    DEBUG=(bool, False)
)
"""
content = re.sub(r'from pathlib import Path', import_block, content, count=1)

# Read .env file
read_env = """
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Take environment variables from .env file
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))
"""
content = re.sub(r"# Build paths inside the project like this: BASE_DIR / 'subdir'.\nBASE_DIR = Path\(__file__\).resolve\(\).parent.parent", read_env, content, count=1)

# 2. Replace SECRET_KEY and DEBUG
content = re.sub(r"SECRET_KEY = '.*?'", "SECRET_KEY = env('SECRET_KEY')", content)
content = re.sub(r"DEBUG = True", "DEBUG = env('DEBUG')", content)

# 3. Replace DATABASES block
new_databases = """DATABASES = {
    'default': env.db(default='postgres://postgres:123@localhost:5432/pobon_maker_backend')
}"""
content = re.sub(r"DATABASES = \{\n\s+'default': \{\n[\s\S]*?\n\s+\}\n\}", new_databases, content)

# 4. Add Throttling to REST_FRAMEWORK
if "REST_FRAMEWORK" in content:
    old_rf = "'DEFAULT_AUTHENTICATION_CLASSES': (\n        'rest_framework_simplejwt.authentication.JWTAuthentication',\n    )"
    new_rf = """'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '10/min',
        'user': '100/min'
    },
    'EXCEPTION_HANDLER': 'core.exceptions.custom_exception_handler'"""
    content = content.replace(old_rf, new_rf)

with open(settings_path, 'w') as f:
    f.write(content)

print("settings.py refactored successfully.")
