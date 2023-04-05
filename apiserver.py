# -*- coding: utf-8 -*-
import bottle
import json
from bottle import route, run, response, post, get, request
from login import login, getKlass, json_serial,  getNarvaro


@route('/narvaro', method=['OPTIONS'])
def option():
    return ""

@get('/narvaro')
def narvaro():
    try:
      (user, password) = request.auth
    except Exception as pwd:
      response.set_header("WWW-Authenticate", 'Basic realm="Restricted"')
      response.status = 401
      return ""
    try:
      s = login(user,password)
    except Exception as e:
     response.set_header("WWW-Authenticate", 'Basic realm="Restricted"')
     response.status = 401
     return str(e)
    klass = getKlass(s)
    for i, elev in enumerate(klass):
      klass[i]["tider"] = getNarvaro(s, elev["uuid"])
    response.content_type = 'application/json'
    return json.dumps({"klass":klass}, default=json_serial)

run(host='localhost', port=8567)
