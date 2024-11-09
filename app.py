from flask import Flask
app = Flask(_name_)
@app.route('/')
def home():
    return """
    <html>
      <head>
        <title>Hello, Flask!</title>
      </head>
      <body>
        <h1>Hello, World!</h1>
        <p>Welcome to your Flask-powered webpage!</p>
      </body>
    </html>
    """

if _name_ == '_main_':
    app.run(debug=True, host='0.0.0.0')
