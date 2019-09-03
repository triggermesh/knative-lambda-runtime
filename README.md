![TriggerMesh Knative Lambda Runtime](./triggermeshklr.png "TriggerMesh Knative Lambda Runtime")

Knative Lambda Runtimes (e.g KLR, pronounced _clear_) are Tekton [Tasks](https://github.com/tektoncd/pipeline/blob/master/docs/tasks.md) that can be used to run an AWS Lambda function in a Kubernetes cluster installed with Knative.

The execution environment where the AWS Lambda function runs is a clone of the AWS Lambda cloud environment thanks to a custom [AWS runtime interface](https://github.com/triggermesh/aws-custom-runtime) and some inspiration from the [LambCI](https://github.com/lambci/docker-lambda) project.

With these templates, you can run your AWS Lambda functions **as is** in a Knative powered Kubernetes cluster.

The examples below use the [tm](https://github.com/triggermesh/tm/releases/latest) CLI to interact with Knative but one could also use `kubectl`.

### Docker registry for builds

To combine the runtime with your source, the examples below produce a new Docker image each time.
While these images can be considered temporary,
builds must be pushed to a Docker registry in order for Kubernetes to be able to pull.
By default `tm` uses [Knative Local Registry](https://github.com/triggermesh/knative-local-registry),
equivalent to adding `--registry-host knative.registry.svc.cluster.local` to the commands below,
so that builds can run without registry authentication.
To override, set `--registry-secret` according to [tm docs](https://github.com/triggermesh/tm#docker-registry).

### Concurrency 

Concurrency in KLR represented by two components: parallel running [bootstrap](https://docs.aws.amazon.com/lambda/latest/dg/runtimes-custom.html) processes per container and Knative [container concurrency](https://github.com/knative/serving/blob/master/docs/spec/spec.md#revision) model. By default [AWS runtime interface](https://github.com/triggermesh/aws-custom-runtime) fires up 8 bootstrap processes (functions, in other words) and allows multiple concurrent requests (`containerConcurrency: 0`) to be handled by each container. Default concurrency configuration can be changed on function deployment or update using `tm deploy service` command parameters:

`--concurrency <N>` - sets Knative service `containerConcurrency` value to `N`

`--build-argument INVOKER_COUNT=<N>` - passes number of parallel running functions to AWS lambda runtime

Values for these two parameters should be calculated individually for each function and depends on operation characteristics. Knative [autoscaling](https://github.com/knative/docs/blob/master/docs/serving/samples/autoscale-go/README.md) is another important factor that affects service performance, but right now KLR uses default autoscaling configuration.


### Examples

NOTE: all examples below work with [Local Registry](https://github.com/triggermesh/knative-local-registry). If you don't have local registry in knative cluster, you can use external registry as discribed in CLI [documentation](https://github.com/triggermesh/tm#docker-registry)


#### Python

1. Install runtime

```
tm deploy task -f https://raw.githubusercontent.com/triggermesh/knative-lambda-runtime/master/python-3.7/runtime.yaml
```

2. Deploy [function](https://github.com/serverless/examples/tree/master/aws-python-simple-http-endpoint)

```
tm deploy service python-test -f https://github.com/serverless/examples \
                              --build-template knative-python37-runtime \
                              --build-argument DIRECTORY=aws-python-simple-http-endpoint \
                              --build-argument HANDLER=handler.endpoint \
                              --wait
```

3. Execute function via public URL

```
curl python-test.default.dev.triggermesh.io

{"statusCode": 200, "body": "{\"message\": \"Hello, the current time is 06:45:49.174383\"}"}
```


To use Python 2.7 runtime simply replace version tag in step 1 and 2 with `python-2.7` and `knative-python27-runtime` accordingly.


#### Nodejs

1. Install node 4.3 runtime

```
tm deploy task -f https://raw.githubusercontent.com/triggermesh/knative-lambda-runtime/master/node-4.x/runtime.yaml
```

2. Deploy example function

```
tm deploy service node4-test -f https://github.com/serverless/examples \
                             --build-template knative-node4-runtime \
                             --build-argument DIRECTORY=aws-node-serve-dynamic-html-via-http-endpoint \
                             --build-argument HANDLER=handler.landingPage \
                             --wait
```

3. Function is ready

```
curl http://node43-test.default.dev.triggermesh.io

{"statusCode":200,"headers":{"Content-Type":"text/html"},"body":"\n  <html>\n    <style>\n      h1 { color: #73757d; }\n    </style>\n    <body>\n      <h1>Landing Page</h1>\n      <p>Hey Unknown!</p>\n    </body>\n  </html>"}
```

#### Node 10 with `async` handler

1. Prepare function code

```
mkdir example-lambda-nodejs
cd example-lambda-nodejs
cat > handler.js <<EOF
async function justWait() {
  return new Promise((resolve, reject) => setTimeout(resolve, 100));
}

module.exports.sayHelloAsync = async (event) => {
  await justWait();
  return {hello: event && event.name || "Missing a name property in the event's JSON body"};
};
EOF

node -e "require('./handler').sayHelloAsync({}).then(h => console.log(h))"
```

2. Install node-10.x runtime

```
tm deploy task -f https://raw.githubusercontent.com/triggermesh/knative-lambda-runtime/master/node-10.x/runtime.yaml
```

3. Deploy function

```
tm deploy service node-lambda -f . --build-template knative-node10-runtime \
                                   --build-argument HANDLER=handler.sayHelloAsync \
                                   --wait
```

Done:

```
curl http://node-lambda.default.dev.triggermesh.io --data '{"name": "Foo"}'
# {"hello":"Foo"}
```

#### Go

1. Prepare function code

You will create a `main.go` file in the `example-lambda-go` directory.

Create the directory and get into it:

```
mkdir example-lambda-go
cd example-lambda-go
```

Copy and Paste the following into a `main.go` file:

```
package main

import (
        "fmt"
        "context"
        "github.com/aws/aws-lambda-go/lambda"
)

type MyEvent struct {
        Name string `json:"name"`
}

func HandleRequest(ctx context.Context, name MyEvent) (string, error) {
        return fmt.Sprintf("Hello %s!", name.Name ), nil
}

func main() {
        lambda.Start(HandleRequest)
}
```

2. Install Go runtime

```
tm deploy task -f https://raw.githubusercontent.com/triggermesh/knative-lambda-runtime/master/go-1.x/runtime.yaml
```

3. Deploy function

```
tm deploy service go-lambda -f . --build-template knative-go-runtime --wait
```

Done:

```
curl http://go-lambda.default.dev.triggermesh.io --data '{"Name": "Foo"}'
"Hello Foo!"
```

##### Dependecies

To have more control over the go project dependecies, KLR runtime will read and "ensure" `Gopkg.toml` file if it's available in the project's root. Without toml file, only `go get` will be executed before build.
If the project has dependencies stored in a private repository, you can create k8s secret with SSH key that will be used for `git clone` operation:

```
cat ~/.ssh/id_rsa | tm set git-auth
```
where `~/.ssh/id_rsa` is a path to SSH private key associated with your git account

#### Ruby

1. Install Ruby 2.5 runtime

```
tm deploy task -f https://raw.githubusercontent.com/triggermesh/knative-lambda-runtime/master/ruby-2.5/runtime.yaml
```

2. Deploy example function

```
tm deploy service ruby-lambda -f https://github.com/serverless/examples --build-argument DIRECTORY=aws-ruby-simple-http-endpoint --build-argument HANDLER=handler.endpoint --build-template knative-ruby25-runtime --wait
```

3. Function is ready

```
curl http://ruby-test-25.default.dev.triggermesh.io
{"statusCode":200,"body":"{\"date\":\"2019-01-14 19:10:29 +0000\"}"}
```

### Support

We would love your feedback on this tool so don't hesitate to let us know what is wrong and how we could improve it, just file an [issue](https://github.com/triggermesh/knative-lambda-runtime/issues/new)

### Code of Conduct

This plugin is by no means part of [CNCF](https://www.cncf.io/) but we abide by its [code of conduct](https://github.com/cncf/foundation/blob/master/code-of-conduct.md)
