#!/usr/bin/env python
from gevent import monkey
import django.core.handlers.wsgi
from socketio.server import SocketIOServer
import os
import sys


# use gevent to patch the standard lib to get async support
monkey.patch_all()

PORT = 8000
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "flowershop.settings")

application = django.core.handlers.wsgi.WSGIHandler()

from flowershop import settings
# add our project directory to the path
sys.path.insert(0, os.path.join(settings.PROJECT_ROOT, "../"))

# add our apps directory to the path 
# sys.path.insert(0, os.path.join(settings.PROJECT_ROOT, "apps"))

if __name__ == '__main__':
    # Launch the redis server in the background
    # print os.popen('redis-s2 &')
    print('Listening on http://127.0.0.1:%s and on port 843 (flash policy server)' % PORT)
    SocketIOServer(('', PORT), application, resource="socket.io").serve_forever()