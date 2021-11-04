# Copyright 2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.

class LambdaHandler
    attr_reader :handler_file_name, :handler_method_name
  
    def initialize(env_handler:)
      handler_split = env_handler.split('.')
      if handler_split.size == 2
        @handler_file_name, @handler_method_name = handler_split
      elsif handler_split.size == 3
        @handler_file_name, @handler_class, @handler_method_name = handler_split
      else
        raise ArgumentError.new("Invalid handler #{handler_split}, must be of form FILENAME.METHOD or FILENAME.CLASS.METHOD where FILENAME corresponds with an existing Ruby source file FILENAME.rb, CLASS is an optional module/class namespace and METHOD is a callable method. If using CLASS, METHOD must be a class-level method.")
      end
    end
  
    def call_handler(request:, context:)
      begin
        opts = {
          event: request,
          context: context
        }
        if @handler_class
          response = Kernel.const_get(@handler_class).send(@handler_method_name, opts)
        else
          response = __send__(@handler_method_name, opts)
        end
        # serialization can be a part of user code
        response.nil? ? response : AwsLambda::Marshaller.marshall_response(response)
      rescue NoMethodError => e
        # This is a special case of standard error that we want to hard-fail for
        raise LambdaErrors::LambdaHandlerCriticalException.new(e)
      rescue NameError => e
        # This is a special case error that we want to wrap
        raise LambdaErrors::LambdaHandlerCriticalException.new(e)
      rescue StandardError => e
        raise LambdaErrors::LambdaHandlerError.new(e)
      rescue Exception => e
        raise LambdaErrors::LambdaHandlerCriticalException.new(e)
      end
    end
  end
