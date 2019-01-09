# Developing Knative Lambda Runtimes

These runtimes build upon base images produced through the respective folder's `Dockerfile`.
To iterate on them you'll want local push access to the registry that Kaniko builds from.
The regular trick with Miniube, to build on the minikube machine's docker and never actually push to a registry, won't work here because Kaniko needs HTTP access.

With [knative-local-registry](https://github.com/triggermesh/knative-local-registry) in Minikube, including the /etc/hosts update, you can however:

```
eval $(minikube docker-env)
docker build -t knative.registry.svc.cluster.local/triggermesh/knative-lambda-runtime-node10 ./node-10.x/
docker push     knative.registry.svc.cluster.local/triggermesh/knative-lambda-runtime-node10
kubectl apply -f node-10.x/buildtemplate.yaml
tm deploy service node-lambda -f . --build-template knative-node10-runtime --build-argument HANDLER=handler.sayHelloAsync --build-argument BASEIMAGE_REGISTRY=knative.registry.svc.cluster.local
curl http://$(minikube ip):32380 -H 'Host: node-lambda.default.example.com' -d '{"name":"Rebased"}'
```

For remote clusters try port-forwarding to your registry. Push to localhost:port doesn't require https.
However note that with for example Docker for Mac the VM that runs docker might not be able to access the port-forward.
See for example https://github.com/docker/for-mac/issues/1160.

# Python

```
docker build -t knative.registry.svc.cluster.local/triggermesh/knative-lambda-runtime-python37:latest python-3.7/
docker push knative.registry.svc.cluster.local/triggermesh/knative-lambda-runtime-python37:latest
tm deploy service python-test -f https://github.com/serverless/examples --build-template knative-python37-runtime --build-argument DIRECTORY=aws-python-simple-http-endpoint --build-argument HANDLER=handler.endpoint --build-argument BASEIMAGE_REGISTRY=knative.registry.svc.cluster.local
```
