#!/usr/bin/python2.6

import sys
import re
import os
path = re.sub(r'/[^/]+/[^/]+$', '', os.path.abspath(sys.argv[0]))
sys.path.append(path)
os.environ["DJANGO_SETTINGS_MODULE"] = "hautoweb.settings"
import django.core.handlers.wsgi
from concurrence.http import WSGIServer
from concurrence import dispatch, Tasklet
import logging
from hwserver.config import conf, confInt

def setupLogging():
    log = logging.getLogger("")
    log.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    log.addHandler(ch)

app = django.core.handlers.wsgi.WSGIHandler()

def app_wrapper(environ, start_response):
    try:
        return app(environ, start_response)
    except Exception as e:
        print e

def main():
    try:
        setupLogging()
        server = WSGIServer(app_wrapper)
        addr = conf('web', 'addr', '0.0.0.0')
        port = confInt('web', 'port', 8080)
        server.serve((addr, port))
        logging.getLogger("hautowebsrv").info("Serving HTTP at %s:%s", addr, port)
        while True:
            Tasklet.sleep(1)
    except Exception as e:
        logging.exception(e)
        os._exit(1)

dispatch(main)
