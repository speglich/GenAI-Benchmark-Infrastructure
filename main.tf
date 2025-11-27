# This module sets up the networking and a public compute instance in OCI.

# Get availability domains in the specified compartment
data "oci_identity_availability_domains" "ads" {
  compartment_id = var.compartment_ocid
}

# ----- Create SSH key pair and save to local file ----- #

# Create SSH key pair
resource "tls_private_key" "ssh_key" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

# Save private key to a local file
resource "local_file" "private_key" {
  content          = tls_private_key.ssh_key.private_key_pem
  filename         = "${path.root}/keys/${local.environment_name}_private_key.pem"
  file_permission  = "0600"
}

# ----- Set up networking resources ----- #

# Create Virtual Cloud Network (VCN)

resource "oci_core_virtual_network" "vcn" {
  cidr_block     = "10.0.0.0/16"
  compartment_id = var.compartment_ocid
  display_name   = "${local.environment_name}-vcn"
}

# Create Internet Gateway
resource "oci_core_internet_gateway" "igw" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_virtual_network.vcn.id
}

# Create NAT Gateway
resource "oci_core_nat_gateway" "natgw" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_virtual_network.vcn.id
}

# Create Route Tables
resource "oci_core_route_table" "public_rt" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_virtual_network.vcn.id

  route_rules {
    network_entity_id = oci_core_internet_gateway.igw.id
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
  }
}

# Create Route Tables
resource "oci_core_route_table" "private_rt" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_virtual_network.vcn.id

  route_rules {
    network_entity_id = oci_core_nat_gateway.natgw.id
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
  }
}

# Create  Public Subnet
resource "oci_core_subnet" "public_subnet" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_virtual_network.vcn.id
  cidr_block     = "10.0.1.0/24"
  route_table_id = oci_core_route_table.public_rt.id
  prohibit_public_ip_on_vnic = false

  security_list_ids = [oci_core_security_list.public_sl.id]
}

# Create Private Subnet
resource "oci_core_subnet" "private_subnet" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_virtual_network.vcn.id
  cidr_block     = "10.0.2.0/24"
  route_table_id = oci_core_route_table.private_rt.id
  prohibit_public_ip_on_vnic = true
}

# Create Security List with dynamic ingress rules based on exposed_ports variable
resource "oci_core_security_list" "public_sl" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_virtual_network.vcn.id
  display_name   = "${local.environment_name}-public-sl"

  dynamic "ingress_security_rules" {
    for_each = var.exposed_ports
    content {
      protocol = "6" # TCP
      source   = "0.0.0.0/0"
      source_type = "CIDR_BLOCK"

      tcp_options {
        min = ingress_security_rules.value
        max = ingress_security_rules.value
      }
    }
  }

  egress_security_rules {
    protocol    = "all"
    destination = "0.0.0.0/0"
    destination_type = "CIDR_BLOCK"
  }
}

# ----- Create Compute Instance ----- #

# Create a public compute instance
resource "oci_core_instance" "public" {
  compartment_id = var.compartment_ocid
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
  display_name = "${local.environment_name}"
  shape = var.shape

  shape_config {
    ocpus         = var.ocpus
    memory_in_gbs = var.memory_in_gbs
  }

  source_details {
    source_type = "image"
    source_id = var.image_id
    boot_volume_size_in_gbs = var.boot_volume_size_in_gbs
  }

  create_vnic_details {
    subnet_id        = oci_core_subnet.public_subnet.id
    assign_public_ip = true
  }

  metadata = {
    ssh_authorized_keys = tls_private_key.ssh_key.public_key_openssh
  }

  # Resize root filesystem to use full boot volume
  provisioner "remote-exec" {
    inline = [
      "sudo /usr/libexec/oci-growfs -y"
    ]

    connection {
      type        = "ssh"
      user        = var.ssh_user
      private_key = file(local_file.private_key.filename)
      host        = self.public_ip
      timeout     = "60m"
    }
  }

  # Install Ansible using remote-exec provisioner with epel repository
  provisioner "remote-exec" {
    inline = [
      "sudo dnf install -y ansible-core"
    ]

    connection {
      type        = "ssh"
      user        = var.ssh_user
      private_key = file(local_file.private_key.filename)
      host        = self.public_ip
      timeout     = "30m"
    }
  }

  # Ensure directory exists before uploading
  provisioner "remote-exec" {
    inline = [
      "mkdir -p /home/${var.ssh_user}/ansible",
      "mkdir -p /home/${var.ssh_user}/benchmarks"
    ]

    connection {
      type        = "ssh"
      user        = var.ssh_user
      private_key = file(local_file.private_key.filename)
      host        = self.public_ip
      timeout     = "30m"
    }
  }

  # Upload benchmarks directory
  provisioner "file" {
    source      = "${path.root}/benchmarks/"
    destination = "/home/${var.ssh_user}/benchmarks/"

    connection {
      type        = "ssh"
      user        = var.ssh_user
      private_key = file(local_file.private_key.filename)
      host        = self.public_ip
      timeout     = "30m"
    }
  }

  # Upload ansible directory
  provisioner "file" {
    source      = "${path.root}/ansible/"
    destination = "/home/${var.ssh_user}/ansible/"

    connection {
      type        = "ssh"
      user        = var.ssh_user
      private_key = file(local_file.private_key.filename)
      host        = self.public_ip
      timeout     = "30m"
    }
  }

  # Run Ansible playbook using remote-exec provisioner
  provisioner "remote-exec" {
    inline = [
      "echo \"localhost ansible_connection=local\" > /home/${var.ssh_user}/ansible/hosts",
      "ansible-playbook -i /home/${var.ssh_user}/ansible/hosts /home/${var.ssh_user}/ansible/site.yml"
    ]
    connection {
      type        = "ssh"
      user        = var.ssh_user
      private_key = file(local_file.private_key.filename)
      host        = self.public_ip
      timeout     = "30m"
    }
  }
}

# ----- Create IAM Resources for Instance Principal ----- #

# Create Dynamic Group for the compute instance
resource "oci_identity_dynamic_group" "compute_instance_dynamic_group" {
  provider = oci.home_region
  compartment_id = var.tenancy_ocid
  name           = "${local.environment_name}_dynamic_group"
  description    = "Dynamic group for ${local.environment_name} instance"
  matching_rule = "ANY {instance.id = '${oci_core_instance.public.id}'}"
}

# Create Policy to allow Instance Principal access to generative-ai-family
resource "oci_identity_policy" "instance_policy" {
  provider = oci.home_region
  compartment_id = var.tenancy_ocid
  name           = "instance-principal-policy"
  description    = "Permite acesso via Instance Principal"

  statements = [
    "Allow dynamic-group ${oci_identity_dynamic_group.compute_instance_dynamic_group.name} to use generative-ai-family in tenancy"
  ]
}
