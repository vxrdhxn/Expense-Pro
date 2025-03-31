from website import create_app
import sys

# This file is specifically for Vercel deployment
# Vercel looks for an 'app' variable to serve the application
try:
    app = create_app()
    print("Application created successfully", file=sys.stderr)
except Exception as e:
    print(f"Error creating application: {str(e)}", file=sys.stderr)
    raise 