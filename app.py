import pymongo
import motor
import hashlib
import binascii
import signal
import os
import sys
import errno
import functools
from tornado import ioloop, web, gen, escape, httpclient
from datetime import timedelta
import pbkdf2
import string
import getopt
import ConfigParser
import json

PBKDF2_ITER = 10000

is_closing = False
config = {}  # TODO create class
error_codes = {
    100000: "not implemented",
    100001: "internal server error",
    100002: "incorrect RPC call",
    100003: "unknown method",
    100004: "authentication required",
    100005: "permission denied",
    100006: "invalid approval code",
    100007: "username already exists",
    100008: "invalid username/password",
    100009: "old password is invalid",
    100010: "no such user",
    100011: "Fetching of sessions data failed",
    100012: "incorrect ajax call",
    100013: "new and old passwords are the same",
    100014: "incorrect input"
}

templates = {'errors': {}}


def sigHandler(signum, frame):
    global is_closing
    print '\nexiting...'
    is_closing = True
## signal_handler
#############################################################################


def try_exit():
    """
    try_exit should close all unfinished ...
    """
    global is_closing
    if is_closing:
        ioloop.IOLoop.instance().stop()
        print 'exit success'
## try_exit
#############################################################################


def load_config(config_file):
    """
    Tries to open configuration file and load
    parameters from it
    """
    config_file = os.path.realpath(config_file)
    if not os.path.exists(config_file):
        raise OSError(errno.ENOENT, os.strerror(errno.ENOENT), config_file)

    cfg = ConfigParser.ConfigParser()

    cfg.read(config_file)

    par = {}
    par.update(cfg.items('main_section'))
    par.update(cfg.items('server_section'))

    return par
## load_config
#############################################################################


class Sessions(dict):
    def __init__(self, *args, **kwargs):
        self.by_username = {}
        super(Sessions, self).__init__(*args, **kwargs)

    def __getattr__(self, name):
        if name == 'by_session_id':
            return self
        super(Sessions, self).__getattr__(name)

    def _common_set(self, session):
        assert isinstance(session, Session)
        username = session.user['username']
        if not username in self.by_username:
            self.by_username[username] = (session,)
        else:
            user_sessions = self.by_username[username]
            for i in range(len(user_sessions)):
                if user_sessions[i].id == session.id:
                    self.by_username[username] = user_sessions[:i] + (session,) + user_sessions[i+1:]
                    break
            else:
                self.by_username[username] += (session,)

    def __setitem__(self, session_id, session):
        self._common_set(session)
        super(Sessions, self).__setitem__(session_id, session)

    def setdefault(self, session_id, default=None):
        session = super(Sessions, self).set_default(session_id, default)
        if not session is default:
            self._common_set(session)
        return session

    def _common_del(self, session):
        assert isinstance(session, Session)
        username = session.user['username']
        user_sessions = self.by_username[username]
        for i in range(len(user_sessions)):
            if user_sessions[i] is session:
                self.by_username[username] = user_sessions[:i] + user_sessions[i+1:]
                break
        else:
            raise AssertionError()
        if not len(self.by_username[username]):
            del self.by_username[username]

    def __delitem__(self, session_id):
        self._common_del(self[session_id])
        super(Sessions, self).__delitem__(session_id)

    def pop(self, session_id, *args, **kwargs):
        session = super(Sessions, self).pop(session_id, *args, **kwargs)
        if not (len(args) and session is args[0]) and not ('default' in kwargs and session is kwargs['default']):
            self._common_del(session)
        return session

    def popitem(self):
        _, session = super(Sessions, self).popitem()
        self._common_del(session)


class Session(object):
    TIMEOUT = 3600
    __slots__ = ['id', 'io_loop', 'timeout', 'user']

    def _expired(self):
        self.unregister()

    def __init__(self, user):
        self.id = None
        self.io_loop = None
        self.timeout = None
        self.user = user

    def register(self, io_loop=None):
        io_loop = io_loop or ioloop.IOLoop.instance()
        for i in range(10):
            id = binascii.hexlify(os.urandom(16))
            if id not in sessions:
                sessions[id] = self
                self.id = id
                break
        if self.id is None:
            raise Exception("failed to register session")
        self.io_loop = io_loop
        self.timeout = self.io_loop.add_timeout(timedelta(seconds=self.TIMEOUT), self._expired)
        print "opened session: " + self.id

    def active(self):
        assert self.id is not None and self.id in sessions
        assert self.io_loop and self.timeout
        self.io_loop.remove_timeout(self.timeout)
        self.timeout = self.io_loop.add_timeout(timedelta(seconds=self.TIMEOUT), self._expired)

    @gen.coroutine
    def update_user(self):
        user = yield db.users.find_one({ 'username': self.user['username'] })
        if not user:
            raise Exception("failed to update user profile")
        self.user = user
# </class Session>


class RPCException(Exception):
    pass
# </class RPCException>


class RPC(object):

    @staticmethod
    @gen.coroutine
    def _delete_user(username, current_session=None):
        try:
            user_sessions = sessions.by_username.get(username, ())
            for session in user_sessions:
                if session is not current_session:
                    session.unregister()
            user = yield db.users.find_one({'username': username})
            if not user:
                raise RPCException({'code':100010, 'message': error_codes[100010]})  # no such user
            res = yield db.users.remove({'_id': user['_id']})
            if res['n'] != 1:
                raise RPCException({'code':100001, 'message': error_codes[100001]}) # internal server error
        except pymongo.errors.OperationFailure:
            raise RPCException({'code':100001, 'message': error_codes[100001]}) # internal server error

    # Decorator for RPC methods
    def RPCMethod(async=False, auth=False, admin=False):
        def decor(f):
            assert (admin and auth) or not admin
            f.RPC = True
            f.async = async
            f.auth = auth
            f.admin = admin
            if async: 
                f = gen.coroutine(f)

            @gen.coroutine
            @functools.wraps(f)
            def wrapper(*args, **kwargs):
                if auth:
                    if 'session_id' in kwargs:
                        session_id = kwargs.pop('session_id')
                        kw = True
                    elif len(args) >= 1:
                        session_id = args[0]
                        kw = False
                    else:
                        raise TypeError("invalid parameters for RPC call")
                    if session_id not in sessions:
                        raise gen.Return({'status': 'error', 'code': 100004, 'message': error_codes[100004]})  # authentication required
                    session = sessions[session_id]
                    session.active()
                    if kw:
                        kwargs['session'] = session
                    else:
                        args[0] = session
                    if admin:
                        if not session.user['admin']:
                            raise gen.Return({'status': 'error', 'code': 100005, 'message': error_codes[100005]})  # permission denied
                if async:
                    res = yield f(*args, **kwargs)
                else:
                    res = f(*args, **kwargs)
                raise gen.Return(res)
            # </wrapper()>
            return staticmethod(wrapper)
        # </decor()>
        return decor
    # </RPCMethod()>

    #################### GUEST ###############################
    @RPCMethod(async=True)
    def register(username, password):
        # IN {"jsonrpc": "2.0", "method": "register", "params": {"username" : "username", "password" : "password"}}
        # OUT {"jsonrpc": "2.0", "method": "register", "params":{"status": "Ok/Error", "message": "success/error code"}}
        if username == "" or password == "":
            raise gen.Return({'status': 'error', 'code': 100014, 'message': error_codes[100014]})  # incorrect input

        user = yield db.users.find_one({'username': username})
        if user:
            raise gen.Return({'status': 'error', 'code': 100007, 'message': error_codes[100007]})  # user already exists

        salt = binascii.hexlify(os.urandom(16))
        pdk = pbkdf2.crypt(password, salt, PBKDF2_ITER)  # 100000 is recommended for SHA256 as of 2013
        user = {'username': username, 'pdk': pdk, 'admin': False, 'active': True}
        yield db.users.save(user)  # this method sets _id in user object
        raise gen.Return({'status': 'ok'})
    # </register()>

    @RPCMethod(async=True)
    def login(username, password):
        # IN {"jsonrpc": "2.0", "method": "login", "params": {"username" : "username", "password" : "password"}}
        # OUT {"jsonrpc": "2.0", "method": "login", "params": {"status" : "Ok/Error", "session_id" : "ssesid", "message" : "success message/error code"}}
        if username == "" or password == "":
            raise gen.Return({'status': 'error', 'code': 100014, 'message': error_codes[100014]})  # incorrect input

        user = yield db.users.find_one({ 'username': username })
        if not user:
            raise gen.Return({'status': 'error', 'code': 100008, 'message': error_codes[100008]})  # invalid username/password

        # get iterations count and salt from stored PDK
        _, _, iterations, salt, _ = user['pdk'].split('$')
        iterations = int(iterations, 16) # convert from hex string

        pdk = pbkdf2.crypt(password, salt, iterations)
        if pdk != user['pdk']:
            raise gen.Return({'status': 'error', 'code': 100008, 'message': error_codes[100008]})  # invalid username/password

        session = Session(user)
        session.register()
        raise gen.Return({'status': 'ok', 'session_id': session.id})
    # </login()>


    @RPCMethod()
    def session_alive(session_id):
        # IN {"jsonrpc": "2.0", "method": "session_alive", "params": {"session_id" : "ssesid"}}
        # OUT {"jsonrpc": "2.0", "method": "session_alive", "params": {"status" : "Ok/Error", "alive": true/false, "message" : "success message/error code"}}
        if session_id in sessions:
            return {'status': 'ok', 'alive': True}
        else:
            return {'status': 'ok', 'alive': False}
    # </session_alive()>


    ################### USER ################################
    @RPCMethod(auth=True)
    def logout(session):
        # IN {"jsonrpc": "2.0", "method": "logout", "params": {"session_id" : "ssesid"}}
        # OUT {"jsonrpc": "2.0", "method": "logout", "params": {"status" : "Ok/Error", "message" : "success message/error code"}}
        session.unregister()
        return {'status': 'ok'}
    # </logout()>

# </class RPCHandlers>


class ErrorHandler(web.ErrorHandler):
    """Generates an error response with status_code for all requests."""
    def write_error(self, status_code, **kwargs):
        try:
            self.finish(templates['errors'][status_code])
        except KeyError:
            super(ErrorHandler, self).write_error(status_code, **kwargs)

# override the tornado.web.ErrorHandler with our default ErrorHandler
web.ErrorHandler = ErrorHandler


class BaseHandler(web.RequestHandler):
    def get_current_user(self):
        session_id = self.get_secure_cookie('session_id')
        if session_id is None or not session_id in sessions:
            self.clear_cookie('session_id')
            return None
        return session_id

    @gen.coroutine
    def get_current_user_object(self):
        try:
            session = sessions[self.current_user]
            user = session.user
            raise gen.Return(user)
        except KeyError:
            raise gen.Return(None)

class LoginHandler(BaseHandler):
    def get(self):
        self.render("webapp/login.html")


class RegisterHandler(BaseHandler):
    def get(self):
        self.render("webapp/register.html")


class AjaxHandler(BaseHandler):

    @web.asynchronous
    @gen.coroutine
    def post(self):
        data = escape.json_decode(self.request.body)

        try:
            method = getattr(RPC, data['method'])
        except KeyError:
            res = {'status': 'error', 'code': 100012, 'message': error_codes[100012]}  # incorrect ajax call
        except AttributeError:
            res = {'status': 'error', 'code': 100003, 'message': error_codes[100003]}  # unknown method
        else:
            if not 'params' in data:
                data['params'] = {}
            if method.auth:
                data['params']['session_id'] = self.current_user
            try:
                res = yield method(**data['params'])
            except Exception:
                res = {'status': 'error', 'code': 100001, 'message': error_codes[100001]}   # internal server error
                self.finish(res)
                raise

            if method == RPC.login and res['status'] == 'ok':
                self.set_secure_cookie('session_id', res['session_id'])

        self.write(res)
        self.add_header('Access-Control-Allow-Origin', '*')
        self.set_header('Content-Type', 'application/json')

    def options(self, *args, **kwargs):
        self.add_header('Access-Control-Allow-Origin', '*')
        self.add_header('Access-Control-Allow-Methods', 'POST')
        self.add_header('Access-Control-Allow-Headers', 'accept, content-type')




class RPCHandler(BaseHandler):

    @web.asynchronous
    @gen.coroutine
    def post(self):
        rpcresult = {}
        data = escape.json_decode(self.request.body)

        try:
            method = getattr(RPC, data['method'])
        except KeyError:
            res = {'status': 'error', 'code': 100002, 'message': error_codes[100002]}  # incorrect RPC call
        except AttributeError:
            res = {'status': 'error', 'code': 100003, 'message': error_codes[100003]}  # unknown method
        else:
            try:
                if type(data['params']) == list:
                    data['params'] = data['params'][0]
                res = yield method(**data['params'])
            except Exception:
                res = {'status': 'error', 'code': 100001, 'message': error_codes[100001]}  # internal server error
                rpcresult["error"] = res
                self.finish(rpcresult)
                raise
        if res["status"] == 'error':
            rpcresult["error"] = res
        else:
            rpcresult["result"] = res
        self.write(rpcresult)
        self.add_header('Access-Control-Allow-Origin', '*')
        self.set_header('Content-Type', 'application/json')

    def options(self, *args, **kwargs):
        self.add_header('Access-Control-Allow-Origin', '*')
        self.add_header('Access-Control-Allow-Methods', 'POST')
        self.add_header('Access-Control-Allow-Headers', 'accept, content-type')


class ConfigFileHandler(web.StaticFileHandler):
    def initialize(self, path):

        self.dirname, self.filename = os.path.split(path)
        super(ConfigFileHandler, self).initialize(self.dirname)

    def get(self, path=None, include_body=True):
        # Ignore 'path'.
        super(ConfigFileHandler, self).get(self.filename, include_body)

    def get_content_type(self):
        mime_type = super(ConfigFileHandler, self).get_content_type()
        if mime_type is None:
            mime_type = "application/octet-stream"
        return mime_type


class MainHandler(BaseHandler):
    @web.authenticated
    @web.asynchronous
    @gen.coroutine
    def get(self):
        user = yield self.get_current_user_object()
        self.render("webapp/index.html", user=user["username"])

settings = {
    "cookie_secret": "61oETzKXQOGaYdkL5gEmGeJJFuYh7EQnp2CdTP1o/Vo=",
    "login_url": "/login",
    "debug": True,
}

client = motor.MotorClient()
db = 'localhost:27017'
sessions = Sessions()

application = web.Application([
    (r"/login", LoginHandler),
    (r"/register", RegisterHandler),
    (r"/ajax", AjaxHandler),
    (r"/rpc", RPCHandler),
    (r"/", MainHandler),
    (r"/(.*)", web.StaticFileHandler, {"path": "./webapp/"}),
    (r"/(favicon.ico)",  web.StaticFileHandler, {"path": "./webapp/"})
], **settings)

signal.signal(signal.SIGINT, sigHandler)


def RunApp(arguments=""):
    global config
    global db
    if "config" in arguments.keys() != False:
        config_file = arguments["config"]
    else:
        config_file = 'config.cfg'

    try:
        config = load_config(config_file)
    except OSError, e:
        print "Failed to load parameters from %s" % config_file
        sys.exit(1)
    db = client[config["db_name"]]
    port = config["webapp_port"]
    address = config["webapp_address"]
    application.listen(port, address)


    ioloop.PeriodicCallback(try_exit, 100).start()
    ioloop.IOLoop.instance().start()
## RunApp
#############################################################################

if __name__ == "__main__":
    #Parse Args
    arguments = {}
    try:
        opts, args = getopt.getopt(sys.argv[1:], "c:")
    except getopt.GetoptError as e:
        print "Got error while parsing args: %s " % e
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-c':
            arguments["config"] = arg

    # load templates
    with open('./webapp/404.html', 'rb') as _f:
        templates['errors'][404] = _f.read()

    RunApp(arguments)