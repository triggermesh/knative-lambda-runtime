// Copyright 2019 TriggerMesh, Inc
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

package main

import (
	"bytes"
	"fmt"
	"io/ioutil"
	"net"
	"net/http"
	"net/rpc"
	"os"
	"os/exec"
	"strconv"
	"syscall"
	"time"

	"github.com/aws/aws-lambda-go/lambda/messages"
)

const (
	initErrPath = "/2018-06-01/runtime/init/error"
	invokePath  = "/2018-06-01/runtime/invocation"
	lambdaPort  = "5432"
)

func main() {
	apiURL := "http://" + os.Getenv("AWS_LAMBDA_RUNTIME_API")
	handler := os.Getenv("_HANDLER")
	os.Setenv("PATH", os.Getenv("PATH")+":/opt")

	cmd := exec.Command(handler)
	cmd.Stdout = os.Stderr
	cmd.Stderr = os.Stderr
	cmd.SysProcAttr = &syscall.SysProcAttr{Setpgid: true}
	cmd.Env = append(os.Environ(),
		"_LAMBDA_SERVER_PORT="+lambdaPort,
	)

	if err := cmd.Start(); err != nil {
		sendResponse(apiURL+initErrPath, err.Error())
		return
	}

	defer syscall.Kill(-cmd.Process.Pid, syscall.SIGKILL)

	var conn net.Conn
	var err error
	for {
		if conn, err = net.Dial("tcp", ":"+lambdaPort); err == nil {
			break
		}
		if oerr, ok := err.(*net.OpError); ok {
			if oerr.Op == "dial" && oerr.Net == "tcp" {
				time.Sleep(5 * time.Millisecond)
				continue
			}
		}
		sendResponse(apiURL+initErrPath, err.Error())
		return
	}

	client := rpc.NewClient(conn)
	defer client.Close()

	for {
		if err := client.Call("Function.Ping", messages.PingRequest{}, &messages.PingResponse{}); err == nil {
			break
		}
		time.Sleep(5 * time.Millisecond)
	}

	for {
		request, err := getRequest(apiURL + invokePath + "/next")
		if err != nil {
			sendResponse(apiURL+initErrPath, err.Error())
			continue
		}

		responseURL := apiURL + invokePath + "/" + request.RequestId
		response := messages.InvokeResponse{}
		if err := client.Call("Function.Invoke", request, &response); err != nil {
			sendResponse(responseURL+"/error", err.Error())
			continue
		}
		if response.Error != nil {
			sendResponse(responseURL+"/error", response.Error.Message)
			continue
		}
		sendResponse(responseURL+"/response", string(response.Payload))
	}
}

func getRequest(url string) (*messages.InvokeRequest, error) {
	response, err := http.Get(url)
	if err != nil {
		return nil, err
	}
	defer response.Body.Close()
	data, err := ioutil.ReadAll(response.Body)
	if err != nil {
		return nil, err
	}
	deadline, err := strconv.Atoi(response.Header.Get("Lambda-Runtime-Deadline-Ms"))
	if err != nil {
		return nil, err
	}
	request := &messages.InvokeRequest{
		Payload:            data,
		RequestId:          response.Header.Get("Lambda-Runtime-Aws-Request-Id"),
		InvokedFunctionArn: response.Header.Get("Lambda-Runtime-Invoked-Function-Arn"),
		XAmznTraceId:       response.Header.Get("Lambda-Runtime-Trace-Id"),
		Deadline: messages.InvokeRequest_Timestamp{
			Seconds: int64(deadline),
		},
	}
	return request, nil
}

func sendResponse(url, message string) {
	jsonErr := []byte(message)
	req, err := http.NewRequest("POST", url, bytes.NewBuffer(jsonErr))
	if err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
	client := &http.Client{}
	if _, err := client.Do(req); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}
