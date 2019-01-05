![TriggerMesh Knative Lambda Runtime](./triggermeshklr.png "TriggerMesh Knative Lambda Runtime")

Knative Lambda Runtimes (e.g KLR, pronounced _clear_) are Knative [build templates](https://github.com/knative/build-templates) that can be used to run an AWS Lambda function in a Kubernetes cluster installed with Knative.

The execution environment where the AWS Lambda function runs is a clone of the AWS Lambda cloud environment thanks to a custom [AWS runtime interface](https://github.com/triggermesh/aws-custom-runtime) and some inspiration from the [LambCI](https://github.com/lambci/docker-lambda) project.

With these templates, you can run your AWS Lambda functions **as is** in a Knative powered Kubernetes cluster.

The examples below use the [tm](https://github.com/triggermesh/tm) CLI to interactive with Knative but one could also use `kubectl`:

### Python

1. Install buildtemplate

```
tm deploy buildtemplate -f https://raw.githubusercontent.com/triggermesh/knative-lambda-runtime/master/python-3.7/buildtemplate.yaml
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


### Nodejs

1. Install node 4.3 buildtemplate

```
tm deploy buildtemplate -f https://raw.githubusercontent.com/triggermesh/knative-lambda-runtime/master/node-4.x/buildtemplate.yaml
```

2. Deploy example function

```
tm deploy service node4-test -f https://github.com/serverless/examples --build-template aws-node4-runtime --build-argument DIRECTORY=aws-node-serve-dynamic-html-via-http-endpoint --build-argument HANDLER=handler.landingPage --wait
```

3. Function is ready

```
curl http://node43-test.default.dev.triggermesh.io

{"statusCode":200,"headers":{"Content-Type":"text/html"},"body":"\n  <html>\n    <style>\n      h1 { color: #73757d; }\n    </style>\n    <body>\n      <h1>Landing Page</h1>\n      <p>Hey Unknown!</p>\n    </body>\n  </html>"}
```

### Support

We would love your feedback on this tool so don't hesitate to let us know what is wrong and how we could improve it, just file an [issue](https://github.com/triggermesh/knative-lambda-runtime/issues/new)

### Code of Conduct

This plugin is by no means part of [CNCF](https://www.cncf.io/) but we abide by its [code of conduct](https://github.com/cncf/foundation/blob/master/code-of-conduct.md)
