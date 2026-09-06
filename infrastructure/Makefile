.PHONY: help check init clean download upload all test apply destroy plan git-remote pull-model network-setup

.DEFAULT_GOAL: help
.PRECIOUS: imports.tf terraform.tfvars

CMD=$(shell which tofu || which terraform)
ECHO=$(shell which figlet || which echo)
GITIGNORE_URL=https://www.toptal.com/developers/gitignore/api/terraform,visualstudiocode,direnv

.gitignore:
	curl $(GITIGNORE_URL) > $@

.git: .gitignore
	git init

all: init download apply

test: init download plan

init: check .terraform ## Fetch files from S3 and init

download: clean imports.tf terraform.tfvars ## Refetch the imports and vars

help: ## Display this help
	@$(ECHO) Infrastructure
	@echo Options:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
	@echo
	@cat README.md

.terraform: imports.tf terraform.tfvars
	$(CMD) init \
		-backend-config="key=${TERAFORM_BUCKET_PATH}/state.tfstate" \
		-backend-config="bucket=${TERAFORM_BUCKET}" \
		-backend-config="region=${TERAFORM_BUCKET_REGION}"
	@touch $@

imports.tf:
	@aws s3 cp s3://${TERAFORM_BUCKET}/${TERAFORM_BUCKET_PATH}/$@ . || touch $@

terraform.tfvars:
	@aws s3 cp s3://${TERAFORM_BUCKET}/${TERAFORM_BUCKET_PATH}/$@ . || touch $@

upload: imports.tf terraform.tfvars ## Upload the imports and vars to S3
	@for f in $^; do aws s3 cp $$f s3://${TERAFORM_BUCKET}/${TERAFORM_BUCKET_PATH}/$$f; done

check: ## Check the env vars are set
ifndef TERAFORM_BUCKET
	$(error "TERAFORM_BUCKET is required!")
endif
ifndef TERAFORM_BUCKET_REGION
	$(error "TERAFORM_BUCKET_REGION is required!")
endif
ifndef TERAFORM_BUCKET_PATH
	$(error "TERAFORM_BUCKET_PATH is required!")
endif

clean: ## Remove fetched files
	@rm -f imports.tf terraform.tfvars

apply: check .terraform ## Apply the terraform
	$(CMD) apply

destroy: check .terraform ## Destroy the terraform
	$(CMD) destroy

plan: check .terraform ## Plan the terraform
	$(CMD) plan

git-remote: ## Add the git remote
	@git -C .. remote remove dokku 2>/dev/null || true
	git -C .. remote add dokku $(shell $(CMD) output -raw git-remote)

network-setup: ## Attach both apps to the private network (the provider cannot)
	$(eval HOST := $(shell $(CMD) output -raw hosting-domain))
	$(eval NET := $(shell $(CMD) output -raw private-network))
	@ssh dokku@$(HOST) network:create $(NET) 2>/dev/null || true
	@# attach-post-create only. initial-network REPLACES the default bridge,
	@# which cuts the app off from the Postgres container on 172.17.0.0/16.
	@for app in canidoit ollama; do \
		ssh dokku@$(HOST) network:set $$app attach-post-create $(NET); \
	done
	@echo "Rebuilding both apps so they pick the network up..."
	@for app in canidoit ollama; do ssh dokku@$(HOST) ps:rebuild $$app; done

pull-model: ## Pull the model into the ollama app (one-off, after first apply)
	# `run` would start a fresh container with no server to talk to, so the
	# pull has to happen inside the running web container.
	ssh dokku@$(shell $(CMD) output -raw hosting-domain) enter ollama web ollama pull $(shell $(CMD) output -raw llm-model)
