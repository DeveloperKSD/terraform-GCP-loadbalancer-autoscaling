resource "google_compute_region_instance_group_manager" "mig" {
  name   = "web-mig"
  region = var.region

  base_instance_name = "web"
  
  version {
    instance_template = google_compute_instance_template.web_template.id
  }

  named_port {
    name = "http"
    port = 80
  }

  auto_healing_policies {
    health_check      = google_compute_health_check.http_hc.id
    initial_delay_sec = 60
  }
}