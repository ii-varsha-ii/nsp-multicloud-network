variable "aws_region" {
  description = "aws regions"
  default     = "us-east-1"
}

variable "vpc_name_tag" {
  description = "Name of the VPC"
}

variable "vpc_1_cidr_block" {
  description = "VPC CIDR block"
}

variable "public_subnet_cidr" {
  description = "Public Subnet CIDR block"
}

variable "private_subnet_cidr" {
  description = "Private Subnet CIDR block"
}
variable "public_subnet_name_tag" {
  description = "Public Subnet Name Tag"
}
variable "private_subnet_name_tag" {
  description = "Private Subnet Name Tag"
}

variable "aws_asn" {
  description = "AWS ASN"
  default = 64512
}

# -------------------------------------------------
# AZURE
# -------------------------------------------------

variable "azure_bgp_asn" {
  description = "Azure BGP ASN"
}

variable "azure_vpc_cidr_block" {
  description = "Azure VPN gateway"
}

variable "azure_subnet_cidr_block" {
  description = "Azure Private Subnet CIDR block"
}

variable "azure_gateway_subnet_cidr_block" {
  description = "Azure Gateway Subnet CIDR block"
}

variable "tunnel1_inside_cidr" {
  description = "AWS Tunnel 1 CIDR"
}
variable "tunnel2_inside_cidr" {
  description = "AWS Tunnel 2 CIDR"
}
variable "ike_version" {
  description = "IKE Version for Tunnels"
  default = ["ikev2"]
}
variable "tunnel_startup_action" {
  description = "Startup Action"
  default = "start"
}

variable "azure_location" {
  description = "Azure location"
  default = "East US"
}

variable "azure_vpn_gateway_sku" {
  description = "VPN Gateway SKU"
  default = "VpnGw2"
}

variable "azure_vpn_gateway_generation" {
  description = "VPN Gateway Generation"
  default = "Generation2"
}

variable "azure_vpn_gateway_primary_ip_name" {
  description = "VPN Gateway Primary IP Name"
}

variable "azure_vpn_gateway_secondary_ip_name" {
  description = "VPN Gateway Secondary IP Name"
}

variable "apipa_addresses_primary" {
  description = "APIPA Addresses Primary IP"
  default = ["169.254.21.2", "169.254.22.2"]
}

variable "apipa_addresses_secondary" {
  description = "APIPA Addresses Secondary IP"
  default = ["169.254.21.6", "169.254.22.6"]
}

variable "local_gateway_1_bgp_peer" {
  description = "BGP Peering address"
  default = "169.254.21.1"
}