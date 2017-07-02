from gevent.wsgi import WSGIServer
from gevent.pool import Pool
from gevent.monkey import patch_all; patch_all()
import socket
from chatbot import libchatbot
import urlparse

consumer = libchatbot()
consumer("Hi")
print 'done'

def application(env, start_response):
    qs = urlparse.parse_qs(env['QUERY_STRING'])
    print qs
    start_response('200 OK', [('Content-Type', 'text/text')])
    result = consumer(qs['string'])
    print result
    yield result

listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
listener.bind(('', 9000))
listener.listen(8)
def serve_forever(listener):
    WSGIServer(listener, application, spawn=Pool(), log=None).serve_forever()

serve_forever(listener)
