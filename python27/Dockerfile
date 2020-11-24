FROM alpine:3 as downloader

RUN apk --no-cache add curl \
 && DOWNLOAD_URL=$(curl -sSf https://api.github.com/repos/triggermesh/aws-custom-runtime/releases/latest | grep "browser_download_url.*-linux-amd64" | cut -d: -f 2,3 | tr -d \") \
 && curl -sSfL ${DOWNLOAD_URL} -o /opt/aws-custom-runtime \
 && chmod +x /opt/aws-custom-runtime

FROM python:2.7-alpine

WORKDIR /opt

COPY / /opt/
COPY --from=downloader /opt/aws-custom-runtime /opt/

ENV LAMBDA_TASK_ROOT "/opt"
