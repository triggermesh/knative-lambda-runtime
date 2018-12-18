### AWS Lambda Python buildtemplates

Knative buildtemplate based on [LambCI](https://github.com/lambci/docker-lambda) Python runtimes. 
Function deployment example using [tm](https://github.com/triggermesh/tm) CLI:

#### Example

Python 3.7

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


To use Python 2.7 runtime simply replace version tag in step 1 and 2 with `python-2.7` and `aws-python27-runtime` accordingly.



### Support

We would love your feedback on this tool so don't hesitate to let us know what is wrong and how we could improve it, just file an [issue](https://github.com/triggermesh/aws-python-runtime/issues/new)

### Code of Conduct

This plugin is by no means part of [CNCF](https://www.cncf.io/) but we abide by its [code of conduct](https://github.com/cncf/foundation/blob/master/code-of-conduct.md)
