"""
Copyright (c) 2018 Amazon. All rights reserved.
"""

import httplib
from collections import defaultdict


class InvocationRequest(object):
    def __init__(self, **kwds):
        self.__dict__.update(kwds)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


class LambdaRuntimeClientError(Exception):
    def __init__(self, endpoint, response_code, response_body):
        self.endpoint = endpoint
        self.response_code = response_code
        self.response_body = response_body
        super().__init__("Request to Lambda Runtime {} endpoint failed. Reason: {}. Response body: {}".format(endpoint, response_code, response_body))


class LambdaRuntimeClient(object):
    LAMBDA_RUNTIME_API_VERSION = '2018-06-01'

    def __init__(self, lambda_runtime_address):
        self.runtime_connection = httplib.HTTPConnection(lambda_runtime_address)
        self.runtime_connection.connect()

        lambda_runtime_base_path = "/{}".format(self.LAMBDA_RUNTIME_API_VERSION)
        self.init_error_endpoint = "{}/runtime/init/error".format(lambda_runtime_base_path)
        self.next_invocation_endpoint = "{}/runtime/invocation/next".format(lambda_runtime_base_path)
        self.response_endpoint = "{}/runtime/invocation/{{}}/response".format(lambda_runtime_base_path)
        self.error_response_endpoint = "{}/runtime/invocation/{{}}/error".format(lambda_runtime_base_path)

    def post_init_error(self, error_response_data):
        endpoint = self.init_error_endpoint
        self.runtime_connection.request("POST", endpoint, error_response_data)
        response = self.runtime_connection.getresponse()
        response_body = response.read()

        if response.status != httplib.ACCEPTED:
            raise LambdaRuntimeClientError(endpoint, response.status, response_body)

    def wait_next_invocation(self):
        endpoint = self.next_invocation_endpoint
        self.runtime_connection.request("GET", endpoint)
        response = self.runtime_connection.getresponse()
        response_body = response.read()
        headers = defaultdict(lambda: None, {k: v for k, v in response.getheaders()})

        if response.status != httplib.OK:
            raise LambdaRuntimeClientError(endpoint, response.status, response_body)

        result = InvocationRequest(
            invoke_id=headers["lambda-runtime-aws-request-id"],
            x_amzn_trace_id=headers["lambda-runtime-trace-id"],
            invoked_function_arn=headers["lambda-runtime-invoked-function-arn"],
            deadline_time_in_ms=int(headers["lambda-runtime-deadline-ms"]),
            client_context=headers["lambda-runtime-client-context"],
            cognito_identity=headers["lambda-runtime-cognito-identity"],
            event_body=response_body
        )


        return result

    def post_invocation_result(self, invoke_id, result_data):
        endpoint = self.response_endpoint.format(invoke_id)
        self.runtime_connection.request("POST", endpoint, result_data)
        response = self.runtime_connection.getresponse()
        response_body = response.read()

        if response.status != httplib.ACCEPTED:
            raise LambdaRuntimeClientError(endpoint, response.status, response_body)

    def post_invocation_error(self, invoke_id, error_response_data):
        endpoint = self.error_response_endpoint.format(invoke_id)
        self.runtime_connection.request("POST", endpoint, error_response_data)
        response = self.runtime_connection.getresponse()
        response_body = response.read()

        if response.status != httplib.ACCEPTED:
            raise LambdaRuntimeClientError(endpoint, response.status, response_body)
