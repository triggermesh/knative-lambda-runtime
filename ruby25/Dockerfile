FROM lambci/lambda:ruby2.5 as lambda
FROM alpine:3 as downloader

RUN apk --no-cache add curl \
 && DOWNLOAD_URL=$(curl -sSf https://api.github.com/repos/triggermesh/aws-custom-runtime/releases/latest | grep "browser_download_url.*-linux-amd64" | cut -d: -f 2,3 | tr -d \") \
 && curl -sSfL ${DOWNLOAD_URL} -o /opt/aws-custom-runtime \
 && chmod +x /opt/aws-custom-runtime

FROM ruby:2.5-alpine

WORKDIR /opt

ENV RUBYLIB "/opt"
ENV LAMBDA_TASK_ROOT "/opt"

COPY --from=downloader /opt/aws-custom-runtime /opt/
COPY --from=lambda /var/runtime/lib /opt
COPY lambda_context.rb lambda_handler.rb /opt/

RUN mv /opt/runtime.rb /opt/bootstrap
RUN sed -i /opt/lambda_server.rb -e 's|http://127.0.0.1:9001/2018-06-01|http://127.0.0.1/2018-06-01|'
