var fs = require('fs')
var crypto = require('crypto')

var HANDLER = process.env.AWS_LAMBDA_FUNCTION_HANDLER || process.env._HANDLER || 'index.handler'
var EVENT_ID = process.argv[2] || process.env.AWS_LAMBDA_EVENT_ID
var EVENT_BODY = process.argv[3] || process.env.AWS_LAMBDA_EVENT_BODY || '{}'

var FN_NAME = process.env.AWS_LAMBDA_FUNCTION_NAME || 'test'
var VERSION = process.env.AWS_LAMBDA_FUNCTION_VERSION || '$LATEST'
var MEM_SIZE = process.env.AWS_LAMBDA_FUNCTION_MEMORY_SIZE || '1536'
var TIMEOUT = process.env.AWS_LAMBDA_FUNCTION_TIMEOUT || '300'
var REGION = process.env.AWS_REGION || process.env.AWS_DEFAULT_REGION || 'us-east-1'
var ACCOUNT_ID = process.env.AWS_ACCOUNT_ID || randomAccountId()
var ACCESS_KEY_ID = process.env.AWS_ACCESS_KEY_ID || 'SOME_ACCESS_KEY_ID'
var SECRET_ACCESS_KEY = process.env.AWS_SECRET_ACCESS_KEY || 'SOME_SECRET_ACCESS_KEY'
var SESSION_TOKEN = process.env.AWS_SESSION_TOKEN
var INVOKED_ARN = process.env.AWS_LAMBDA_FUNCTION_INVOKED_ARN || arn(REGION, ACCOUNT_ID, FN_NAME)

function consoleLog(str) {
  process.stderr.write(formatConsole(str))
}

function systemLog(str) {
  process.stderr.write(formatSystem(str) + '\n')
}

function systemErr(str) {
  process.stderr.write(formatErr(str) + '\n')
}

function handleResult(resultStr, cb) {
  if (!process.stdout.write(resultStr + '\n')) {
    process.stdout.once('drain', cb)
  } else {
    process.nextTick(cb)
  }
}

// Don't think this can be done in the Docker image
process.umask(2)

process.env.AWS_LAMBDA_FUNCTION_NAME = FN_NAME
process.env.AWS_LAMBDA_FUNCTION_VERSION = VERSION
process.env.AWS_LAMBDA_FUNCTION_MEMORY_SIZE = MEM_SIZE
process.env.AWS_LAMBDA_LOG_GROUP_NAME = '/aws/lambda/' + FN_NAME
process.env.AWS_LAMBDA_LOG_STREAM_NAME = new Date().toISOString().slice(0, 10).replace(/-/g, '/') +
  '/[' + VERSION + ']' + crypto.randomBytes(16).toString('hex')
process.env.AWS_REGION = REGION
process.env.AWS_DEFAULT_REGION = REGION
process.env._HANDLER = HANDLER

var OPTIONS = {
  initInvokeId: EVENT_ID,
  invokeId: EVENT_ID,
  handler: HANDLER,
  suppressInit: true,
  credentials: {
    key: ACCESS_KEY_ID,
    secret: SECRET_ACCESS_KEY,
    session: SESSION_TOKEN,
  },
  eventBody: EVENT_BODY,
  contextObjects: {
    // clientContext: '{}',
    // cognitoIdentityId: undefined,
    // cognitoPoolId: undefined,
  },
  invokedFunctionArn: INVOKED_ARN,
}

// Some weird spelling error in the source?
OPTIONS.invokeid = OPTIONS.invokeId

var invoked = false
var errored = false
var start = null

module.exports = {
  initRuntime: function() { return OPTIONS },
  waitForInvoke: function(fn) {
    if (invoked) return
    start = process.hrtime()
    invoked = true
    fn(OPTIONS)
  },
  reportRunning: function(invokeId) {}, // eslint-disable-line no-unused-vars
  reportDone: function(invokeId, errType, resultStr) {
    if (!invoked) return

    var exitCode = errored || errType ? 1 : 0
    if (typeof resultStr === 'string') {
      handleResult(resultStr, function() { process.exit(exitCode) })
    } else {
      process.exit(exitCode)
    }
  },
  reportFault: function(invokeId, msg, errName, errStack) {
    errored = true
    systemErr(msg + (errName ? ': ' + errName : ''))
    if (errStack) systemErr(errStack)
  },
  reportUserInitStart: function() {},
  reportUserInitEnd: function() {},
  reportUserInvokeStart: function() {},
  reportUserInvokeEnd: function() {},
  reportException: function() {},
  sendConsoleLogs: consoleLog,
  maxLoggerErrorSize: 256 * 1024,
}

function formatConsole(str) {
  return str.replace(/^[0-9TZ:.-]+\t[0-9a-f-]+\t/, '\u001b[34m$&\u001b[0m')
}

function formatSystem(str) {
  return '\u001b[32m' + str + '\u001b[0m'
}

function formatErr(str) {
  return '\u001b[31m' + str + '\u001b[0m'
}

function hrTimeMs(hrtime) {
  return (hrtime[0] * 1e9 + hrtime[1]) / 1e6
}

function hrTimeMs(hrtime) {
  return (hrtime[0] * 1e9 + hrtime[1]) / 1e6
}

function randomAccountId() {
  return String(0x100000000 * Math.random())
}

function arn(region, accountId, fnName) {
  return 'arn:aws:lambda:' + region + ':' + accountId.replace(/[^\d]/g, '') + ':function:' + fnName
}
