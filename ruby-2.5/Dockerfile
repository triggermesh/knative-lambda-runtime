FROM lambci/lambda:ruby2.5
FROM ruby:2.5-alpine
WORKDIR /opt
        
RUN apk --no-cache add curl \
    && API_VERSION=$(curl -sI https://github.com/triggermesh/aws-custom-runtime/releases/latest | grep "Location:" | awk -F "/" '{print $NF}' | tr -d "\r") \
    && curl -sL https://github.com/triggermesh/aws-custom-runtime/releases/download/${API_VERSION}/aws-custom-runtime > aws-custom-runtime \
    && chmod +x aws-custom-runtime

ENV RUBYLIB "/opt"
ENV LAMBDA_TASK_ROOT "/opt"
        
COPY --from=0 /var/runtime/lib /opt
RUN mv /opt/runtime.rb /opt/bootstrap
RUN sed -i /opt/lambda_server.rb -e 's|http://127.0.0.1:9001/2018-06-01|http://127.0.0.1/2018-06-01|'