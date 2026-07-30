import os

settings_path = r'c:\Users\atika\Documents\hridoy\my-project_new_eddition\sports-go\pobon_maker_backend\pobon_maker_backend\settings.py'

with open(settings_path, 'r') as f:
    content = f.read()

# Replace INSTALLED_APPS
old_apps_end = """    'rest_framework',
    'corsheaders',
]"""

new_apps_end = """    'rest_framework',
    'corsheaders',
    'rest_framework_simplejwt',
    'accounts',
]"""

content = content.replace(old_apps_end, new_apps_end)

# Add REST_FRAMEWORK settings if not present
if "REST_FRAMEWORK" not in content:
    content += "\n\nREST_FRAMEWORK = {\n"
    content += "    'DEFAULT_AUTHENTICATION_CLASSES': (\n"
    content += "        'rest_framework_simplejwt.authentication.JWTAuthentication',\n"
    content += "    )\n"
    content += "}\n"

with open(settings_path, 'w') as f:
    f.write(content)
print("Settings updated successfully.")
