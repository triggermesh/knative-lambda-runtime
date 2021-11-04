"""
Copyright (c) 2018 Amazon. All rights reserved.
"""

import decimal
import json
import logging
import os
import site
import sys
import time
import traceback
import warnings
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    import imp

from lambda_runtime_client import LambdaRuntimeClient


class FaultData(object):
    """
    Contains three fields, msg, except_value, and trace
    msg is mandatory and must be a string
    except_value and trace are optional and must be a string or None.

    The constructor will convert all values to strings through str().
    In addition, the constructor will try to join iterable trace values with "\n".join.
    """

    def __init__(self, msg, except_value=None, trace=None):
        if not (trace is None or isinstance(trace, str)):
            try:
                trace = "\n".join(trace)
            except TypeError:
                trace = str(trace)
        self.msg = str(msg)
        self.except_value = except_value if except_value is None else str(except_value)
        self.trace = trace


class FaultException(Exception):
    def __init__(self, msg, except_value=None, trace=None):
        error_data = FaultData(msg, except_value, trace)
        self.msg = error_data.msg
        self.except_value = error_data.except_value
        self.trace = error_data.trace


def _get_handler(handler):
    try:
        (modname, fname) = handler.rsplit('.', 1)
    except ValueError as e:
        fault = FaultException("Bad handler '{}'".format(handler), str(e), None)
        request_handler = make_fault_handler(fault)
        return request_handler

    file_handle, pathname, desc = None, None, None
    try:
        # Recursively loading handler in nested directories
        for segment in modname.split('.'):
            if pathname is not None:
                pathname = [pathname]
            file_handle, pathname, desc = imp.find_module(segment, pathname)
        if file_handle is None:
            module_type = desc[2]
            if module_type == imp.C_BUILTIN:
                fault = FaultException("Cannot use built-in module {} as a handler module".format(modname), None, None)
                request_handler = make_fault_handler(fault)
                return request_handler
        m = imp.load_module(modname, file_handle, pathname, desc)
    except ImportError as e:
        fault = FaultException("Unable to import module '{}'".format(modname), str(e), None)
        request_handler = make_fault_handler(fault)
        return request_handler
    except SyntaxError as e:
        trace = "File \"%s\" Line %s\n\t%s" % (e.filename, e.lineno, e.text)
        fault = FaultException("Syntax error in module '{}'".format(modname), str(e), trace)
        request_handler = make_fault_handler(fault)
        return request_handler
    finally:
        if file_handle is not None:
            file_handle.close()

    try:
        request_handler = getattr(m, fname)
    except AttributeError as e:
        fault = FaultException("Handler '{}' missing on module '{}'".format(fname, modname), str(e), None)
        request_handler = make_fault_handler(fault)
    return request_handler


class number_str(float):
    def __init__(self, o):
        self.o = o

    def __repr__(self):
        return str(self.o)


def decimal_serializer(o):
    if isinstance(o, decimal.Decimal):
        return number_str(o)
    raise TypeError(repr(o) + " is not JSON serializable")


def make_fault_handler(fault):
    def result(*args):
        raise fault

    return result


def try_or_raise(function, error_message):
    try:
        return function()
    except Exception as e:
        pass
        #raise JsonError(sys.exc_info(), error_message)


def make_error(errorMessage, errorType, stackTrace):  # stackTrace is an array
    result = {}
    if errorMessage:
        result['errorMessage'] = errorMessage
    if errorType:
        result['errorType'] = errorType
    if stackTrace:
        result['stackTrace'] = stackTrace
    return result


def to_json(obj):
    return json.dumps(obj, default=decimal_serializer)


def handle_event_request(lambda_runtime_client, request_handler, invoke_id, event_body, client_context_json, cloudevents_context_json, cognito_identity_json, invoked_function_arn, epoch_deadline_time_in_ms):
    error_result = None
    try:
        client_context = None
        if client_context_json:
            client_context = try_or_raise(lambda: json.loads(client_context_json), "Unable to parse client context json")
        cloudevents_context = None
        if cloudevents_context_json:
            cloudevents_context = try_or_raise(lambda: json.loads(cloudevents_context_json), "Unable to parse cloudevents context json")
        cognito_identity = None
        if cognito_identity_json:
            cognito_identity = try_or_raise(lambda: json.loads(cognito_identity_json), "Unable to parse cognito identity json")
        context = LambdaContext(invoke_id, client_context, cloudevents_context, cognito_identity, epoch_deadline_time_in_ms, invoked_function_arn)
        json_input = try_or_raise(lambda: json.loads(event_body.decode()), "Unable to parse input as json")
        result = request_handler(json_input, context)
        if result is not None:
            result = try_or_raise(lambda: to_json(result), "An error occurred during JSON serialization of response")
    except FaultException as e:
        error_result = make_error(e.msg, None, None)
        error_result = to_json(error_result)
    except JsonError as e:
        error_result = build_fault_result(invoke_id, e.exc_info, e.msg)
        error_result = to_json(error_result)
    except Exception as e:
        error_result = build_fault_result(invoke_id, sys.exc_info(), None)
        error_result = to_json(error_result)

    if error_result is not None:
        lambda_runtime_client.post_invocation_error(invoke_id, error_result)
    else:
        lambda_runtime_client.post_invocation_result(invoke_id, result)


def build_fault_result(invoke_id, exc_info, msg):
    etype, value, tb = exc_info
    if msg:
        msgs = [msg, str(value)]
    else:
        msgs = [str(value), etype.__name__]

    tb_tuples = extract_traceback(tb)

    for i in range(len(tb_tuples)):
        if "/bootstrap.py" not in tb_tuples[i][0]:  # filename of the tb tuple
            tb_tuples = tb_tuples[i:]
            break

    return make_error(str(value), etype.__name__, traceback.format_list(tb_tuples))


def extract_traceback(tb):
    frames = traceback.extract_tb(tb)

    # Python3 returns a list of SummaryFrames instead of a list of tuples
    # for traceback.extract_tb() calls.
    # To make it consistent, we map the list of frames to a list of tuples just like python2

    frames = [(frame.filename, frame.lineno, frame.name, frame.line) for frame in frames]

    return frames


class CognitoIdentity(object):
    __slots__ = ["cognito_identity_id", "cognito_identity_pool_id"]


class Client(object):
    __slots__ = ["installation_id", "app_title", "app_version_name", "app_version_code", "app_package_name"]


class ClientContext(object):
    __slots__ = ['custom', 'env', 'client']


def make_obj_from_dict(_class, _dict, fields=None):
    if _dict is None:
        return None
    obj = _class()
    set_obj_from_dict(obj, _dict)
    return obj


def set_obj_from_dict(obj, _dict, fields=None):
    if fields is None:
        fields = obj.__class__.__slots__
    for field in fields:
        setattr(obj, field, _dict.get(field, None))


class LambdaContext(object):
    def __init__(self, invoke_id, client_context, cloudevents_context, cognito_identity, epoch_deadline_time_in_ms, invoked_function_arn=None):
        self.aws_request_id = invoke_id
        self.log_group_name = os.environ.get('AWS_LAMBDA_LOG_GROUP_NAME')
        self.log_stream_name = os.environ.get('AWS_LAMBDA_LOG_STREAM_NAME')
        self.function_name = os.environ.get("AWS_LAMBDA_FUNCTION_NAME")
        self.memory_limit_in_mb = os.environ.get('AWS_LAMBDA_FUNCTION_MEMORY_SIZE')
        self.function_version = os.environ.get('AWS_LAMBDA_FUNCTION_VERSION')
        self.invoked_function_arn = invoked_function_arn
        self.ce = cloudevents_context

        self.client_context = make_obj_from_dict(ClientContext, client_context)
        if self.client_context is not None:
            self.client_context.client = make_obj_from_dict(Client, self.client_context.client)

        self.identity = make_obj_from_dict(CognitoIdentity, {})
        if cognito_identity is not None:
            self.identity.cognito_identity_id = cognito_identity.get("cognitoIdentityId")
            self.identity.cognito_identity_pool_id = cognito_identity.get("cognitoIdentityPoolId")

        self._epoch_deadline_time_in_ms = epoch_deadline_time_in_ms

    def get_remaining_time_in_millis(self):
        epoch_now_in_ms = int(time.time() * 1000)
        delta_ms = self._epoch_deadline_time_in_ms - epoch_now_in_ms
        return delta_ms if delta_ms > 0 else 0

    def log(self, msg):
        sys.stdout.write(str(msg))


class LambdaLoggerHandler(logging.Handler):
    def __init__(self):
        logging.Handler.__init__(self)

    def emit(self, record):
        msg = self.format(record)
        print(msg)


class LambdaLoggerFilter(logging.Filter):
    def filter(self, record):
        record.aws_request_id = _GLOBAL_AWS_REQUEST_ID or ""
        return True


class JsonError(Exception):
    def __init__(self, exc_info, msg):
        self.exc_info = exc_info
        self.msg = msg


class Unbuffered(object):
    def __init__(self, stream):
        self.stream = stream

    def __getattr__(self, attr):
        return getattr(self.stream, attr)

    def write(self, msg):
        self.stream.write(msg)
        self.stream.flush()

    def writelines(self, msgs):
        self.stream.writelines(msgs)
        self.stream.flush()

def is_pythonpath_set():
    return "PYTHONPATH" in os.environ


def get_opt_site_packages_directory():
    return '/opt/python/lib/python{}.{}/site-packages'.format(sys.version_info.major, sys.version_info.minor)


def get_opt_python_directory():
    return '/opt/python'


def set_path_env_variable():
    DEFAULT_PATH_ENV = "/usr/local/bin:/usr/bin/:/bin"
    if os.environ.get('PATH') is None or os.environ["PATH"] == DEFAULT_PATH_ENV:
        os.environ["PATH"] = ":".join(["/var/lang/bin", DEFAULT_PATH_ENV])


# set default sys.path for discoverability
# precedence: /var/task -> /opt/python/lib/pythonN.N/site-packages -> /opt/python
def set_default_sys_path():
    if not is_pythonpath_set():
        sys.path.insert(0, get_opt_python_directory())
        sys.path.insert(0, get_opt_site_packages_directory())
    # '/var/task' is function author's working directory
    # we add it first in order to mimic the default behavior of populating sys.path and make modules under '/var/task'
    # discoverable - https://docs.python.org/3/library/sys.html#sys.path
    sys.path.insert(0, os.environ['LAMBDA_TASK_ROOT'])


def add_default_site_directories():
    # Set '/var/task as site directory so that we are able to load all customer .pth files
    site.addsitedir(os.environ["LAMBDA_TASK_ROOT"])
    if not is_pythonpath_set():
        site.addsitedir(get_opt_site_packages_directory())
        site.addsitedir(get_opt_python_directory())


def set_ld_library_path_variable():
    if os.environ.get('LD_LIBRARY_PATH') is None:
        ld_library_path = "/var/lang/lib:/lib64:/usr/lib64"

        if os.environ.get('LAMBDA_RUNTIME_DIR') is not None:
            runtime_dir = os.environ['LAMBDA_RUNTIME_DIR']
            runtime_dir_lib = os.path.join(runtime_dir, 'lib')
            ld_library_path = ":".join([ld_library_path, runtime_dir, runtime_dir_lib])

        if os.environ.get('LAMBDA_TASK_ROOT') is not None:
            task_dir = os.environ['LAMBDA_TASK_ROOT']
            task_dir_lib = os.path.join(task_dir, 'lib')
            ld_library_path = ":".join([ld_library_path, task_dir, task_dir_lib])

        os.environ["LD_LIBRARY_PATH"] = ld_library_path

def update_xray_env_variable(xray_trace_id):
    if xray_trace_id is not None:
        os.environ['_X_AMZN_TRACE_ID'] = xray_trace_id
    else:
        if '_X_AMZN_TRACE_ID' in os.environ:
            del os.environ['_X_AMZN_TRACE_ID']

_GLOBAL_AWS_REQUEST_ID = None


def main():
    sys.stdout = Unbuffered(sys.stdout)
    sys.stderr = Unbuffered(sys.stderr)

    lambda_runtime_api_addr = os.environ['AWS_LAMBDA_RUNTIME_API']
    del os.environ['AWS_LAMBDA_RUNTIME_API']
    lambda_runtime_client = LambdaRuntimeClient(lambda_runtime_api_addr)

    try:
        set_path_env_variable()
        set_ld_library_path_variable()

        logging.Formatter.converter = time.gmtime
        logger = logging.getLogger()
        logger_handler = LambdaLoggerHandler()
        logger_handler.setFormatter(logging.Formatter(
            '[%(levelname)s]\t%(asctime)s.%(msecs)dZ\t%(aws_request_id)s\t%(message)s\n',
            '%Y-%m-%dT%H:%M:%S'
        ))
        logger_handler.addFilter(LambdaLoggerFilter())
        logger.addHandler(logger_handler)

        global _GLOBAL_AWS_REQUEST_ID

        set_default_sys_path()
        add_default_site_directories()

        handler = os.environ["_HANDLER"]
        request_handler = _get_handler(handler)
    except Exception as e:
        result = build_fault_result(None, sys.exc_info(), None)
        result = to_json(result)

        lambda_runtime_client.post_init_error(result)

        sys.exit(1)

    while True:
        event_request = lambda_runtime_client.wait_next_invocation()

        _GLOBAL_AWS_REQUEST_ID = event_request.invoke_id

        update_xray_env_variable(event_request.x_amzn_trace_id)

        handle_event_request(lambda_runtime_client,
                             request_handler,
                             event_request.invoke_id,
                             event_request.event_body,
                             event_request.client_context,
                             event_request.cloudevents_context,
                             event_request.cognito_identity,
                             event_request.invoked_function_arn,
                             event_request.deadline_time_in_ms)
