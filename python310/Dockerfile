FROM alpine as downloader

RUN apk --no-cache add curl git \
 && DOWNLOAD_URL=$(curl -sSf https://api.github.com/repos/triggermesh/aws-custom-runtime/releases/latest | grep "browser_download_url.*-linux-amd64" | cut -d: -f 2,3 | tr -d \") \
 && curl -sSfL ${DOWNLOAD_URL} -o /opt/aws-custom-runtime \
 && chmod +x /opt/aws-custom-runtime \
 && git clone https://github.com/triggermesh/eventstore-python-client.git /opt/client

FROM amazon/aws-lambda-python:3.10

WORKDIR /opt

RUN pip install --upgrade pip \
 && pip install grpcio grpcio-tools

RUN mv /var/runtime/bootstrap /opt

COPY --from=downloader /opt/client/eventstore /opt/eventstore
COPY --from=downloader /opt/aws-custom-runtime /opt/

ENV PYTHONPATH "/opt/eventstore"
ENV LAMBDA_TASK_ROOT "/opt"
