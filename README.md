### AWS Lambda Python buildtemplates

#### Python 3.7

Knative buildtemplate based on [LambCI](https://github.com/lambci/docker-lambda) Python 3.7 runtime. 
Function deployment example using [tm](https://github.com/triggermesh/tm) CLI:

1. Install buildtemplate

```
tm deploy buildtemplate -f https://raw.githubusercontent.com/triggermesh/aws-python-runtime/master/python-3.7/buildtemplate.yaml
```

2. Deploy [function](https://github.com/serverless/examples/tree/master/aws-python-simple-http-endpoint)

```
tm deploy service python-test -f https://github.com/serverless/examples --build-template aws-python37-runtime --build-argument DIRECTORY=aws-python-simple-http-endpoint --build-argument HANDLER=handler.endpoint --wait
```

3. Execute function via public URL

```
curl python-test.default.dev.triggermesh.io
{"statusCode": 200, "body": "{\"message\": \"Hello, the current time is 06:45:49.174383\"}"}
```

#### Python 2.7

TODO

#### Nodejs

TODO