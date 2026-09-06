# canidoit infrastructure

OpenTofu (or Terraform) for the Dokku host: the Django app, Postgres, and the
self-hosted model it generates answers with.

State lives in S3. Secrets live in `terraform.tfvars`, which is fetched from
the same bucket by `make download` and never committed.

    export TERAFORM_BUCKET=...
    export TERAFORM_BUCKET_REGION=...
    export TERAFORM_BUCKET_PATH=...

    make all        # init, download, apply
    make test       # init, download, plan

## Variables

`terraform.tfvars` must set these (no defaults):

    domain               # apex domain, no www
    hosting_domain       # the Dokku host, also the CNAME target
    zoneid               # Cloudflare zone ID
    cloudflare_api_token # needs DNS:Edit on that zone
    secret_key           # Django SECRET_KEY

These default sensibly and only need setting to override:
`site_verb` (`do`), `llm_model` (`qwen2.5:0.5b-instruct-q4_K_M`),
`private_network` (`canidoit-internal`).

## First deploy, in order

    make all              # apps, Postgres, DNS
    make network-setup    # private network, see below
    make git-remote       # adds the dokku remote
    git push dokku main   # the actual code deploy
    make pull-model       # weights, see below

`network-setup` must run after the apply, because it configures apps that the
apply creates. It rebuilds ollama, since a container only joins a network when
it starts.

Nothing serves real answers until the pool has been filled, so finish with:

    ssh dokku@<hosting_domain> run canidoit python manage.py topup_responses

Until that worker has caught up the site falls back to the hardcoded refusals
in `core/answers.py`, so it is never broken, just repetitive.

## Why the network is not in the terraform

`aliksend/dokku` 1.0.24 cannot set network properties on Dokku >= 0.35. It
sends its own schema field names (`initial_network`) where dokku expects the
hyphenated property (`initial-network`), and dokku now rejects those:

    Invalid property specified, valid properties include: attach-post-create,
    attach-post-deploy, bind-all-interfaces, initial-network, ...

1.0.24 is the latest release, so there is nothing to upgrade to. `make
network-setup` does the same work over SSH instead. If the provider is ever
fixed, the `networks` blocks can go back into `canidoit.tf` and `ollama.tf`.

The host runs Dokku 0.38.21; the provider is only tested to 0.34.7, so treat
other resources as suspect if an apply fails in a similar way.

## Pulling the model

After the first apply, pull the model into the ollama app. Nothing generates
answers until this has run:

    make pull-model

## Shape

`canidoit` is a Dokku app on `www.<domain>`, with a `worker` process running
`db_worker` to generate pooled responses. Code is deployed by pushing to the
Dokku remote, so `deploy` is `null` in the terraform: the apply builds the app
and its config, and `git push dokku main` ships the code. Dokku's other mode,
syncing from a repository URL, would need a remote this project does not have.

`ollama` is a second app deployed straight from `ollama/ollama`. It has no
domains and no port mappings, so it is not routed from the internet — the only
thing that reaches it is `canidoit`, over the `canidoit-internal` network, at
`http://ollama.web:11434`.

The model container is capped with `--memory`. On a 2GB box the resident cost
matters more than reload time, so `OLLAMA_KEEP_ALIVE=0` unloads the model
between generations; generation is queued and infrequent, so this is cheap.
Weights are on a persistent mount, so a redeploy does not re-download them.
