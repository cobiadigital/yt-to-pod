from flask_frozen import Freezer
from doc_blog import create_app

app = create_app()
freezer = Freezer(app)
app.config['FREEZER_BASE_URL'] = 'https://docpod.cobiadigital.com'
app.config['FREEZER_IGNORE_MIMETYPE_WARNINGS'] = True


if __name__ == '__main__':
    freezer.freeze()
