.PHONY: help clean install init css css-watch node
.DEFAULT_GOAL := install
.PRECIOUS: requirements.%.txt

REQS=$(shell python -c "import tomllib; print(' '.join(f'requirements.{k}.txt' for k in tomllib.load(open('pyproject.toml', 'rb')).get('project', {}).get('optional-dependencies', {}).keys()))")

SYSTEM_PYTHON_VERSION:=$(shell ls /usr/bin/python* | grep -Eo '[0-9]+\.[0-9]+' | sort -V | tail -n 1)
UV_PATH:=~/.cargo/bin/uv
VENV_PATH:=.venv
PIP_PATH:=$(VENV_PATH)/bin/pip
WHEEL_PATH:=$(VENV_PATH)/bin/wheel
PRE_COMMIT_PATH:=$(VENV_PATH)/bin/pre-commit

STATIC_DIR:= staticfiles
STATIC_CSS_DIR:= $(STATIC_DIR)/css
BUILD_DIR:= build/css
CSS_FILES:= $(wildcard ./css/*.css ./css/**/*.css)
MAIN_CSS_FILES:= $(subst ./css/,./$(STATIC_CSS_DIR)/,$(subst .css,.min.css,$(wildcard ./css/*.css)))
# Classes Django renders from Python, so purgecss cannot find them in a template.
CSS_SAFELIST:= noun

HTML_FILES:= $(shell find . -type f -name '*.html' -not -path './.venv/*' -not -path './.direnv/*' -not -path './node_modules/*' -not -path './build/*')

help: ## Display this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.gitignore:
	curl -sS "https://www.toptal.com/developers/gitignore/api/visualstudiocode,python,direnv" > $@

.git: .gitignore
	git init

.pre-commit-config.yaml: | $(PRE_COMMIT_PATH) .git
	curl -sS https://gist.githubusercontent.com/bengosney/4b1f1ab7012380f7e9b9d1d668626143/raw/.pre-commit-config.yaml > $@
	$(PRE_COMMIT_PATH) autoupdate
	@touch $@

pyproject.toml: | $(UV_PATH)
	curl -sS https://gist.githubusercontent.com/bengosney/f703f25921628136f78449c32d37fcb5/raw/pyproject.toml > $@
	@touch $@

requirements.%.txt: $(UV_PATH) pyproject.toml
	@echo "Building $@"
	$(UV_PATH) pip compile --generate-hashes -q --extra $* -o $@ $(filter-out $<,$^)

requirements.txt: $(UV_PATH) pyproject.toml
	@echo "Building $@"
	$(UV_PATH) pip compile --generate-hashes -q -o $@ $(filter-out $<,$^)

$(VENV_PATH): | $(UV_PATH) .envrc
	$(UV_PATH) venv --managed-python --python $(SYSTEM_PYTHON_VERSION)
	@touch $@

.git/hooks/pre-commit: .git $(PRE_COMMIT_PATH) .pre-commit-config.yaml
	$(PRE_COMMIT_PATH) install

.envrc:
	@echo "Setting up .envrc then stopping"
	@echo 'if [ ! -d .venv ]; then' > $@
	@echo '    make .venv' >> $@
	@echo 'fi' >> $@
	@echo '' >> $@
	@echo 'PATH_add ".venv/bin"' >> $@
	@echo 'export VIRTUAL_ENV="$$PWD/.venv"' >> $@
	@echo 'export VIRTUAL_ENV_PROMPT="$$(basename $$PWD)"' >> $@
	@echo 'watch_file .venv' >> $@
	@touch -d '+1 minute' $@
	@false

$(UV_PATH):
	@echo "Error: uv is not installed. Install it from https://github.com/astral-sh/uv" && false

$(PRE_COMMIT_PATH): $(UV_PATH) $(VENV_PATH)
	$(UV_PATH) pip install pre-commit

init: .envrc $(UV_PATH) requirements.txt requirements.dev.txt .git/hooks/pre-commit ## Initalise a enviroment

package-lock.json: package.json
	npm install

node_modules: package.json package-lock.json
	npm install
	@touch $@

node: node_modules ## Install the node dependencies

# Bundle the @imports, drop selectors no template uses, then minify.
$(STATIC_CSS_DIR)/%.min.css: css/%.css $(CSS_FILES) $(HTML_FILES) node_modules
	@mkdir -p $(BUILD_DIR)/purged $(STATIC_CSS_DIR)
	./node_modules/.bin/lightningcss --bundle -o $(BUILD_DIR)/$*.css $<
	./node_modules/.bin/purgecss --css $(BUILD_DIR)/$*.css --content $(HTML_FILES) --safelist $(CSS_SAFELIST) -o $(BUILD_DIR)/purged/
	./node_modules/.bin/lightningcss --minify --targets ">= 0.25%" -o $@ $(BUILD_DIR)/purged/$*.css

css: $(MAIN_CSS_FILES) ## Build, purge and minify the css

css-watch: ## Rebuild the css whenever a source file or template changes
	$(MAKE) css
	@while inotifywait -qre close_write ./css $(shell find . -type d -name templates -not -path './node_modules/*'); do \
		$(MAKE) css; \
	done

clean: ## Remove all build files
	find . -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete
	rm -rf .pytest_cache
	rm -f .testmondata
	rm -rf $(BUILD_DIR)

install: $(VENV_PATH) requirements.txt $(REQS) ## Install development requirements (default)
	@echo "Installing $(filter-out $<,$^)"
	$(UV_PATH) pip sync $(filter-out $<,$^)
