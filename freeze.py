from flask_frozen import Freezer
from ai_blog import create_app


app = Flask(__name__)

if __name__ == '__main__':
    Freezer(app).run()