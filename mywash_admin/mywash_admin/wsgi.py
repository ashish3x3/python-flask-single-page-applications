from manage import load_paths, load_urls_and_templates
import settings


load_paths()
from mywash_admin import app, api

load_urls_and_templates(app)
app.debug = app.config['DEBUG']
