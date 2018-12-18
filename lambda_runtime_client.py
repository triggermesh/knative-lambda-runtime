"""
Copyright (c) 2018 Amazon. All rights reserved.
"""

import http.client
import http
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
        super().__init__(f"Request to Lambda Runtime '{endpoint}' endpoint failed. Reason: '{response_code}'. Response body: '{response_body}'")


class LambdaRuntimeClient(object):
    LAMBDA_RUNTIME_API_VERSION = '2018-06-01'

    def __init__(self, lambda_runtime_address):
        self.runtime_connection = http.client.HTTPConnection(lambda_runtime_address)
        self.runtime_connection.connect()

        lambda_runtime_base_path = f'/{self.LAMBDA_RUNTIME_API_VERSION}'
        self.init_error_endpoint = f'{lambda_runtime_base_path}/runtime/init/error'
        self.next_invocation_endpoint = f'{lambda_runtime_base_path}/runtime/invocation/next'
        self.response_endpoint = f'{lambda_runtime_base_path}/runtime/invocation/{{}}/response'
        self.error_response_endpoint = f'{lambda_runtime_base_path}/runtime/invocation/{{}}/error'

    def post_init_error(self, error_response_data):
        endpoint = self.init_error_endpoint
        self.runtime_connection.request("POST", endpoint, error_response_data)
        response = self.runtime_connection.getresponse()
        response_body = response.read()

        if response.code != http.HTTPStatus.ACCEPTED:
            raise LambdaRuntimeClientError(endpoint, response.code, response_body)

    def wait_next_invocation(self):
        endpoint = self.next_invocation_endpoint
        self.runtime_connection.request("GET", endpoint)
        response = self.runtime_connection.getresponse()
        response_body = response.read()
        headers = defaultdict(lambda: None, {k: v for k, v in response.getheaders()})

        if response.code != http.HTTPStatus.OK:
            raise LambdaRuntimeClientError(endpoint, response.code, response_body)

        result = InvocationRequest(
            invoke_id=headers["Lambda-Runtime-Aws-Request-Id"],
            x_amzn_trace_id=headers["Lambda-Runtime-Trace-Id"],
            invoked_function_arn=headers["Lambda-Runtime-Invoked-Function-Arn"],
            deadline_time_in_ms=int(headers["Lambda-Runtime-Deadline-Ms"]),
            client_context=headers["Lambda-Runtime-Client-Context"],
            cognito_identity=headers["Lambda-Runtime-Cognito-Identity"],
            event_body=response_body
        )

        return result

    def post_invocation_result(self, invoke_id, result_data):
        endpoint = self.response_endpoint.format(invoke_id)
        self.runtime_connection.request("POST", endpoint, result_data)
        response = self.runtime_connection.getresponse()
        response_body = response.read()

        if response.code != http.HTTPStatus.ACCEPTED:
            raise LambdaRuntimeClientError(endpoint, response.code, response_body)

    def post_invocation_error(self, invoke_id, error_response_data):
        endpoint = self.error_response_endpoint.format(invoke_id)
        self.runtime_connection.request("POST", endpoint, error_response_data)
        response = self.runtime_connection.getresponse()
        response_body = response.read()

        if response.code != http.HTTPStatus.ACCEPTED:
            raise LambdaRuntimeClientError(endpoint, response.code, response_body)
