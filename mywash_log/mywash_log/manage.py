# Set the path
import os, sys
import os
import sys
# Import the settings
import settings
import importlib
import jinja2
from flask.ext.script import Manager, Command, Shell, Server

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask.ext.script import Manager, Server
from mywash_log import app

manager = Manager(app)


def load_urls_and_templates(app):
    templates_dir_list = []
    this_module = os.path.dirname(__file__).split("/")[-1]

    modules_list = []
    # Load the URLS from urls.py
    for path in os.listdir(settings.BASE_DIR):
        if os.path.isdir(os.path.join(settings.BASE_DIR, path)):
            if os.path.isfile(os.path.join(settings.BASE_DIR, path, "urls.py")):
                if path == this_module:
                    modules_list.append(path)
                else:
                    modules_list.insert(0, path)
    
    for module in modules_list:
        try:
            importlib.import_module("%s.urls" % module)
            print "Imported: %s.urls" % module
        except Exception, e:
            print "Unimported: %s.urls" % module, e

        if os.path.isdir(os.path.join(settings.BASE_DIR, path, 'templates')):
            templates_dir_list.append(os.path.join(settings.BASE_DIR, path, 'templates'))

    # Load the templates in different apps
    app.jinja_loader = jinja2.ChoiceLoader([
        app.jinja_loader,
        jinja2.FileSystemLoader(templates_dir_list)
    ])    


def load_paths():
    # Load project as well
    sys.path.append(settings.BASE_DIR)



class MyServer(Server):
    def __call__(self, app, host, port, use_debugger, use_reloader,
               threaded, processes, passthrough_errors):
        # app.config.from_object(settings)

        app.debug = app.config['DEBUG']
        app.secret_key = app.config['SECRET_KEY']
        load_urls_and_templates(app)

        super(MyServer, self).__call__(app, host, 5003, use_debugger, False,
               threaded, processes, passthrough_errors)
        

class MyShell(Shell):
    def run(self, no_ipython=False):
        # app.config.from_object(settings)

        app.debug = app.config['DEBUG']
        app.secret_key = app.config['SECRET_KEY']

        load_urls_and_templates(app)

        context = self.get_context()
        if not no_ipython:
            try:
                import IPython
                try:
                    sh = IPython.Shell.IPShellEmbed(banner=self.banner)
                except AttributeError:
                    sh = IPython.frontend.terminal.embed.InteractiveShellEmbed(banner1=self.banner)
                sh(global_ns=dict(), local_ns=context)
                return
            except ImportError:
                pass


class CollectStatic(Command):
    def run(self):
        if not os.path.exists(settings.STATIC_ROOT):
            os.mkdir(settings.STATIC_ROOT)

        for path in os.listdir(settings.BASE_DIR):
            file_name = os.path.join(settings.BASE_DIR, path)
            if os.path.isdir(file_name) and file_name != settings.STATIC_ROOT:
                local_static_path = os.path.join(settings.BASE_DIR, path, 'static', "*")
                os.system("rsync -avP %s %s" % (local_static_path, settings.STATIC_ROOT))


if __name__ == '__main__':
    load_paths()
    from mywash_log import app, api

    manager = Manager(app)
    manager.add_command('runserver', MyServer())
    manager.add_command('shell', Shell())
    manager.run()
