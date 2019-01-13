FROM node:4-alpine
WORKDIR /opt

RUN apk --no-cache add curl \
    && API_VERSION=$(curl -sI https://github.com/triggermesh/aws-custom-runtime/releases/latest | grep "Location:" | awk -F "/" '{print $NF}' | tr -d "\r") \
    && RUNTIME_VERSION=$(curl -sI https://github.com/triggermesh/knative-lambda-runtime/releases/latest | grep "Location:" | awk -F "/" '{print $NF}' | tr -d "\r") \
    && curl -sL https://github.com/triggermesh/aws-custom-runtime/releases/download/${API_VERSION}/aws-custom-runtime > aws-custom-runtime \
    && chmod +x aws-custom-runtime \
    && curl -sL https://github.com/triggermesh/knative-lambda-runtime/archive/${RUNTIME_VERSION}.tar.gz | tar -xz knative-lambda-runtime-${RUNTIME_VERSION}/node-4.x \
    && mv knative-lambda-runtime-${RUNTIME_VERSION}/node-4.x/* .

ENV LAMBDA_TASK_ROOT "/opt"
