from website import create_app
import sys

app = create_app()

if __name__ == '__main__':
    try:
        app.run(debug=False)
    except Exception as e:
        print(f"Error running application: {str(e)}", file=sys.stderr)
        raise

# This is for Vercel deployment
app = app