import os
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

@app.route('/health')
def health():
    return "Health check OK"

# No need for the if __name__ == "__main__" block
# flask run will handle this automatically