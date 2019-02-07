## Launching a KLR based function with `tm`

Check the `serverless.yaml` file which describes the function deployment.

See how the Cron Job trigger is defined

```
tm deploy
```

This will do the build of the function in the Knative cluster, deploy it as a Service and create a CronJob event source.
