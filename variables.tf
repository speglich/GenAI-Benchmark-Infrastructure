variable "region" {
  description = "OCI region where resources will be created"
  default     = "sa-saopaulo-1"
  type        = string
}

variable "compartment_ocid" {
  description = "OCID of the compartment where resources will be created"
  type        = string
}

variable "tenancy_ocid" {
  description = "OCID of the OCI tenancy"
  type        = string
}

variable "exposed_ports" {
  description = "List of ports to expose on the instance"
  type        = list(number)
  default     = [22]
}

variable "shape" {
    description = "Shape of the instance (e.g., 'VM.Standard2.1', 'VM.GPU.A10.1')"
    default = "VM.Standard.E5.Flex"
    type   = string
}

variable "ocpus" {
  description = "Number of OCPUs to allocate for the instance (Only for VM shapes)"
  type        = number
  default     = 32
}

variable "memory_in_gbs" {
  description = "Amount of memory in GBs to allocate for the instance (Only for VM shapes)"
  type        = number
  default     = 64
}

variable "image_id" {
    description = "OCID of the image to use for the instance"
    default = "ocid1.image.oc1.sa-saopaulo-1.aaaaaaaa7avt4eh5yycvdmzpenw45offnablkjduihvxhtxoesevvu76n2eq"
    type = string
}

variable "boot_volume_size_in_gbs" {
    description = "Size of the boot volume in GBs"
    default     = 50
    type        = number
}

variable "ssh_user" {
    description = "Default SSH user for accessing the instance"
    default     = "opc"
    type        = string
}
