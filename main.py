from website import create_app
import os
from flask import send_from_directory

app = create_app()

# GitHub Pages configuration
app.config['APPLICATION_ROOT'] = '/Expense-Pro'
app.config['PREFERRED_URL_SCHEME'] = 'https'

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
