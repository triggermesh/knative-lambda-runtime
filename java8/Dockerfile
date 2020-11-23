FROM openjdk:8-jre-alpine

COPY runtime /var/runtime

RUN apk update && apk add --no-cache libc6-compat curl \
    && API_VERSION=$(curl -sI https://github.com/triggermesh/aws-custom-runtime/releases/latest | grep -i "Location:" | awk -F "/" '{print $NF}' | tr -d "\r") \
    && curl -sL https://github.com/triggermesh/aws-custom-runtime/releases/download/${API_VERSION}/aws-custom-runtime-linux-amd64 > /var/runtime/mockserver \
    && chmod +x /var/runtime/mockserver

ENV LD_LIBRARY_PATH /lib64:/usr/lib64:/var/runtime:/var/runtime/lib:/var/task:/var/task/lib:/opt/lib
ENV LAMBDA_RUNTIME_DIR /var/runtime
ENV LAMBDA_TASK_ROOT /var/task
ENV INVOKER_COUNT 0
ENV INTERNAL_API_PORT 9001

WORKDIR "/var/task"

ENTRYPOINT ["/usr/bin/java", \
        "-XX:MaxHeapSize=2834432k", \
        "-XX:MaxMetaspaceSize=163840k", \
        "-XX:ReservedCodeCacheSize=81920k", \
        "-XX:+UseSerialGC", \
        "-Xshare:auto", \
        "-XX:-TieredCompilation", \
        "-jar", \
        "/var/runtime/lib/LambdaJavaRTEntry-1.0.jar"]
