resource "dokku_app" "canidoit" {
  app_name = "canidoit"

  # The apex is here only so Django can redirect it to www (PREPEND_WWW).
  domains = ["www.${var.domain}", var.domain]

  config = {
    DJANGO_SETTINGS_MODULE = "canidoit.settings.prod"
    DJANGO_LOG_LEVEL       = "INFO"
    LOG_LEVEL              = "INFO"

    ALLOWED_HOSTS = "www.${var.domain},${var.domain}"
    BASE_URL      = "https://www.${var.domain}"
    DOMAIN        = "www.${var.domain}"
    SECRET_KEY    = var.secret_key

    SITE_VERB = var.site_verb

    # Reached over the private network, so the model is never public.
    LLM_ENABLED  = "1"
    LLM_BASE_URL = "http://${dokku_app.ollama.app_name}.web:11434"
    LLM_MODEL    = var.llm_model
    LLM_TIMEOUT  = "60"
  }


  ports = {
    80 = {
      scheme         = "http"
      container_port = 8000
    }
  }

  # Deployed by pushing to the Dokku remote (`make git-remote`), so the deploy
  # itself is not managed here. Dokku's other mode, syncing from a repository
  # URL, needs a remote this project does not have.
  deploy = null

  # `networks` is managed by `make network-setup`, because the provider cannot
  # set it on Dokku >= 0.35. Without this, every apply writes null over it and
  # silently detaches the app from the private network.
  lifecycle {
    ignore_changes = [networks]
  }

}

resource "dokku_plugin" "postgres" {
  name = "postgres"
  url  = "https://github.com/dokku/dokku-postgres.git"
}

resource "dokku_postgres" "main_db" {
  service_name = "canidoit"
  image        = "postgres:17.5"

  depends_on = [
    dokku_plugin.postgres
  ]
}

resource "dokku_postgres_link" "canidoit_db_link" {
  app_name     = dokku_app.canidoit.app_name
  service_name = dokku_postgres.main_db.service_name
  alias        = "DATABASE"

  depends_on = [
    dokku_plugin.postgres
  ]
}

output "git-remote" {
  value       = "dokku@${var.hosting_domain}:${dokku_app.canidoit.app_name}"
  description = "Git remote"
  depends_on  = []
}

output "hosting-domain" {
  value       = var.hosting_domain
  description = "Dokku host"
}

output "llm-model" {
  value       = var.llm_model
  description = "Model tag the app generates with"
}

output "private-network" {
  value       = var.private_network
  description = "Dokku network shared by the app and the model"
}
