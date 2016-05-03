from flask import render_template,make_response,request,jsonify,json,abort
from functools import wraps
import logging
from werkzeug.wrappers import BaseResponse


def commonrender(template):
    def decorator(f):
        @wraps(f)
        def render_wrapper(*args,**kwargs):
            params = f(*args,**kwargs)
            if isinstance(params, BaseResponse):
                return params
            elif request.headers.get('Content-type','')=='application/json':
                return jsonify(params)
            elif request.headers.get('Content-type','')=='application/octet-stream':
                return params
            else:
                #logging.info(**params)
                response = make_response(render_template(template,**params));
                response.headers['Cache-Control'] = 'no-store';
                response.headers['Vary'] = 'Accept';
                response.headers["Access-Control-Allow-Origin"]="*"
                response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
                response.headers["Access-Control-Max-Age"] = "1000"
                response.headers["Access-Control-Allow-Headers"] = "Origin, X-Requested-With, Content-Type, Accept"
                return response;
        return render_wrapper
    return decorator

def commonrenderMulti():
    def decorator(f):
        @wraps(f)
        def render_wrapper(*args,**kwargs):
            params = f(*args,**kwargs)
            if request.headers.get('Content-type','')=='application/json':
                return jsonify(params)
            elif request.headers.get('Content-type','')=='application/octet-stream':
                return params
            else:
                try:
                    template = params.get("template")
                    try:
                        response = make_response(render_template(template,**params));
                        response.headers['Cache-Control'] = 'no-cache';
                        response.headers['Vary'] = 'Accept';
                        response.headers["Access-Control-Allow-Origin"]="*"
                        response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
                        response.headers["Access-Control-Max-Age"] = "1000"
                        response.headers["Access-Control-Allow-Headers"] = "Origin, X-Requested-With, Content-Type, Accept"
                        return response;
                    except Exception as e:
                        logging.error("Critical Error Unable to render Template"+ str(e))
                        logging.error(params)
                        abort(404)
                except Exception as e:
                    logging.error("Template missing in response"+ str(e))
                    logging.error(params)
                    abort(404)
        return render_wrapper
    return decorator
