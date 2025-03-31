from website import create_app

app = create_app()

# This is for local development
if __name__ == '__main__':
    app.run(debug=True)

# This is for Vercel deployment
app = app