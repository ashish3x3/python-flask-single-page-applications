#application starts here the app called here is referring to __init__.py in boiler folder
from boiler import app

if __name__ == '__main__':
    if app.debug:
        app.run(host='0.0.0.0', debug=True, port=5001)
    else:
        app.run(host='0.0.0.0')
