FROM alpine as downloader

RUN apk --no-cache add curl \
 && DOWNLOAD_URL=$(curl -sSf https://api.github.com/repos/triggermesh/aws-custom-runtime/releases/latest | grep "browser_download_url.*-linux-amd64" | cut -d: -f 2,3 | tr -d \") \
 && curl -sSfL ${DOWNLOAD_URL} -o /opt/aws-custom-runtime \
 && chmod +x /opt/aws-custom-runtime

FROM amazon/aws-lambda-ruby:3.2

WORKDIR /opt

RUN mv /var/runtime/bootstrap /opt

COPY --from=downloader /opt/aws-custom-runtime /opt/

ENV RUBYLIB "/opt"
ENV LAMBDA_TASK_ROOT "/opt"
