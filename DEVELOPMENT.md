# Developing Knative Lambda Runtimes

These runtimes make use of docker base images.
To develop you need local push access to the registry that kaniko builds from.
The regular trick with miniube, to use the minikube machine's docker, won't work because kaniko needs HTTP access to the image.

For example with [knative-local-registry](https://github.com/triggermesh/knative-local-registry) in Minikube expose it using a nodeport,

```
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: nodeport-for-development
  namespace: registry
spec:
  type: NodePort
  selector:
    app: registry
  ports:
  - nodePort: 32500
    port: 80
EOF
```

If your minikube has `apiserver.service-node-port-range=80-32767` you can use port 80 for `nodePort` and not have to deal with port numbers below.

Now set up a `.local` DNS record so you don't need https to push: `echo "$(minikube ip) ko.local" | sudo tee -a /etc/hosts`
