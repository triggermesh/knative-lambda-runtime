FROM alpine:3 as downloader

RUN apk --no-cache add curl \
 && DOWNLOAD_URL=$(curl -sSf https://api.github.com/repos/triggermesh/aws-custom-runtime/releases/latest | grep "browser_download_url.*-linux-amd64" | cut -d: -f 2,3 | tr -d \") \
 && curl -sSfL ${DOWNLOAD_URL} -o /opt/aws-custom-runtime \
 && chmod +x /opt/aws-custom-runtime

FROM openjdk:8-jre-alpine

RUN apk add --no-cache libc6-compat

COPY runtime /var/runtime
COPY --from=downloader /opt/aws-custom-runtime /var/runtime/mockserver

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
