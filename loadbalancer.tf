resource "google_compute_backend_service" "backend" {
  name          = "web-backend"
  protocol      = "HTTP"
  port_name     = "http"
  health_checks = [google_compute_health_check.http_hc.id]

  backend {
    group = google_compute_region_instance_group_manager.mig.instance_group
  }
}

resource "google_compute_url_map" "url_map" {
  name            = "web-url-map"
  default_service = google_compute_backend_service.backend.id
}

resource "google_compute_target_http_proxy" "proxy" {
  name    = "web-proxy"
  url_map = google_compute_url_map.url_map.id
}

resource "google_compute_global_forwarding_rule" "fr" {
  name       = "web-forwarding-rule"
  target     = google_compute_target_http_proxy.proxy.id
  port_range = "80"
}