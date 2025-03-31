from website import create_app
import sys

try:
    app = create_app()
    print("Application created successfully", file=sys.stderr)
except Exception as e:
    print(f"Error creating application: {str(e)}", file=sys.stderr)
    raise

# This is for local development
if __name__ == '__main__':
    app.run(debug=True)

# This is for Vercel deployment
app = app