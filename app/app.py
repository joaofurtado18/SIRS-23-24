from create_app import create_app
from dotenv import load_dotenv
import os

load_dotenv()

app = create_app()

host = os.getenv('SERVER_HOST')
port = os.getenv('SERVER_PORT')

if __name__ == '__main__':
    context = ('../certificates/cert.pem', '../certificates/key.pem')
    app.run(host, port, debug=True, ssl_context=context)