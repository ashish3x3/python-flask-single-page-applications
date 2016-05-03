from mywash_admin import app
from views import *

app.add_url_rule("/", view_func=admin_base, methods=['GET'])
app.add_url_rule("/logout", view_func=logout, methods=['GET'])
app.add_url_rule("/employee/register", view_func=register_employee, methods=['GET', 'POST'])
app.add_url_rule("/servestache/" + "<string:file_name>", view_func=serve_stache, methods=['GET'])
app.add_url_rule("/<path:restpath>", view_func=admin_base, methods=['GET'])