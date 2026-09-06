resource "cloudflare_record" "www" {
  name            = "www"
  proxied         = true
  type            = "CNAME"
  content         = var.hosting_domain
  zone_id         = var.zoneid
  allow_overwrite = true
}

# Replaces the registrar's parking A record, which Cloudflare proxied to a dead
# origin and answered with 522. Cloudflare flattens this CNAME at the apex.
resource "cloudflare_record" "apex" {
  # Cloudflare returns the apex as the full zone name, not "@", and the provider
  # treats the difference as forcing replacement.
  name            = var.domain
  proxied         = true
  type            = "CNAME"
  content         = var.hosting_domain
  zone_id         = var.zoneid
  allow_overwrite = true
}
