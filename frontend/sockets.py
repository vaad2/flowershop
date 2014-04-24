# -*- coding: utf-8 -*-
import json, gevent
from common.db import mongo_get

from socketio.namespace import BaseNamespace
from socketio.mixins import BroadcastMixin
from socketio.sdjango import namespace

from bson import json_util
from socketio import packet

old_encode = packet.encode

import logging

logger = logging.getLogger('flowershop.views')


@namespace('/manager')
class NSManager(BaseNamespace, BroadcastMixin):
    def recv_connect(self):
        self.emit('init', {'result': 'success', 'data': 'init'})


    def trace(self, msg):
        self.broadcast_event('trace', msg)

    def trace_test(self, msg):
        self.trace(msg)