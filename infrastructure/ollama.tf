# The self-hosted model, as its own Dokku app deployed from an image.
#
# It is deliberately not routed: no domains, no port mappings. The only thing
# that talks to it is the canidoit app, over the shared private network below.

# The provider cannot manage networks on Dokku >= 0.35 at all: it sends the
# schema's underscored field names (initial_network) as dokku property names,
# and dokku only accepts the hyphenated forms. 1.0.24 is the latest release,
# so there is no fix to upgrade to. Both the network and the per-app network
# properties are therefore applied out of band -- see `make network-setup`.
#
variable "private_network" {
  description = "Existing Dokku network shared by the app and the model"
  default     = "canidoit-internal"
}

variable "llm_model" {
  description = "Ollama model tag the worker generates with"
  default     = "qwen2.5:0.5b-instruct-q4_K_M"
}

resource "dokku_app" "ollama" {
  app_name = "ollama"

  # No domains: this must not be reachable from the internet.
  domains = []

  config = {
    OLLAMA_HOST = "0.0.0.0:11434"

    # Unload the model as soon as a generation finishes. Generation is queued
    # and infrequent, so the resident cost matters far more than reload time.
    OLLAMA_KEEP_ALIVE = "0"

    OLLAMA_MAX_LOADED_MODELS = "1"
    OLLAMA_NUM_PARALLEL      = "1"
  }

  # Weights live on the host, so a redeploy does not re-download the model.
  storage = {
    "ollama-models" = {
      mount_path = "/root/.ollama"
    }
  }

  # Literal keys: the provider cannot build this map when a key is
  # interpolated, so the cap is not a variable.
  docker_options = {
    "--memory=1g" = {
      phase = ["deploy", "run"]
    }
    "--memory-swap=1g" = {
      phase = ["deploy", "run"]
    }
  }


  deploy = {
    type          = "docker_image"
    docker_image  = "ollama/ollama:latest"
    allow_rebuild = true
  }

  # `networks` is managed by `make network-setup`, because the provider cannot
  # set it on Dokku >= 0.35. Without this, every apply writes null over it and
  # silently detaches the app from the private network.
  lifecycle {
    ignore_changes = [networks]
  }

}
