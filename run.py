import os
from dotenv import load_dotenv
from app import create_app

load_dotenv('.env.local')

env = os.environ.get('FLASK_ENV', 'dev')
app = create_app(env)

if __name__ == '__main__':
    debug = os.environ.get('FLASK_DEBUG', '1') == '1'
    app.run(debug=debug, host='0.0.0.0', port=5000)

