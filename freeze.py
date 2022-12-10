from flask_frozen import Freezer
from ai_blog import create_app

app = create_app()
freezer = Freezer(app)
app.config['FREEZER_RELATIVE_URLS'] = True
app.config['FREEZER_IGNORE_MIMETYPE_WARNINGS'] = True


if __name__ == '__main__':
    freezer.freeze()
