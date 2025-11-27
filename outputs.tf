
output "instructions" {
  value = <<EOT
To access the GenAI Benchmark instance, use the following command:
ssh -i ${local_file.private_key.filename} ${var.ssh_user}@${oci_core_instance.public.public_ip}
EOT
  description = "Instructions to access the GenAI Benchmark instance."
}