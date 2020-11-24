REPO               = knative-lambda-runtime
REPO_DESC          = TriggerMesh Knative Lambda Runtime
RUNTIMES           = java8 node10 node4 python27 python37 ruby25

BASE_DIR          ?= $(CURDIR)

DOCKER            ?= docker
IMAGE_REPO        ?= gcr.io/triggermesh
IMAGE_TAG         ?= latest
IMAGE_SHA         ?= $(shell git rev-parse HEAD)

.PHONY: help images cloudbuild-test cloudbuild

all: images

help: ## Display this help
	@awk 'BEGIN {FS = ":.*?## "; printf "\n$(REPO_DESC)\nUsage:\n  make \033[36m<source>\033[0m\n"} /^[a-zA-Z0-9._-]+:.*?## / {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

IMAGES = $(foreach r,$(RUNTIMES),$(r).image)
images: $(IMAGES) ## Build the Docker images
$(IMAGES): %.image:
	docker build -t $(IMAGE_REPO)/knative-lambda-$* $*

CLOUDBUILD_TEST = $(foreach r,$(RUNTIMES),$(r).cloudbuild-test)
cloudbuild-test: $(CLOUDBUILD_TEST) ## Test container image build with Google Cloud Build
$(CLOUDBUILD_TEST): %.cloudbuild-test:
	gcloud builds submit $* --config cloudbuild.yaml --substitutions _RUNTIME=knative-lambda-$*,COMMIT_SHA=${IMAGE_SHA},_KANIKO_IMAGE_TAG=_

CLOUDBUILD = $(foreach r,$(RUNTIMES),$(r).cloudbuild)
cloudbuild: $(CLOUDBUILD) ## Build and publish image to GCR
$(CLOUDBUILD): %.cloudbuild:
	gcloud builds submit $* --config cloudbuild.yaml --substitutions _RUNTIME=knative-lambda-$*,COMMIT_SHA=${IMAGE_SHA},_KANIKO_IMAGE_TAG=${IMAGE_TAG}
