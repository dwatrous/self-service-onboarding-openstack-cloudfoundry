# Configure the OpenStack Provider
provider "openstack" {
    user_name  = "${var.os_username}"
    tenant_name = "${var.os_project}"
    password  = "${var.os_password}"
    auth_url  = "https://keystone.domain.com/v2.0"
}

# Create a web server
resource "openstack_compute_instance_v2" "automation-server" {
  name = "onboarding"
  image_id = "IMAGE_GUID"
  flavor_id = "FLAVOR_GUID"
  metadata {
    this = "that"
  }
  key_pair = "keypair"
  floating_ip = "${openstack_networking_floatingip_v2.automation_ip.address}"
  security_groups = ["default", "ssh", "web"]
}

resource "openstack_networking_floatingip_v2" "automation_ip" {
  region = ""
  pool = "ext-net"
}
