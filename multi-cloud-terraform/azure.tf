terraform {
  required_providers {
    azurerm = {
      source = "hashicorp/azurerm"
      version = "=3.0.1"
    }
  }
}

provider "azurerm" {
    version = "=1.21.0"
    client_id = "<your_client_id>"
    client_secret = "<your_client_secret>"
    tenant_id = "<your_tenant_id>"
    subscription_id = "<your_subscription_id>"
}

resource "azurerm_resource_group" "azure_rg" {
  name     = "azure_rg"
  location = var.azure_location
}

resource "azurerm_virtual_network" "azure_virtual_network" {
  name                = "azure_virtual_network"
  location            = var.azure_location
  resource_group_name = azurerm_resource_group.azure_rg.name
  address_space       = [var.azure_vpc_cidr_block]

  subnet {
    name           = "azure_private_subnet"
    address_prefix = var.azure_subnet_cidr_block
  }

  subnet {
    name           = "GatewaySubnet"
    address_prefix = var.azure_gateway_subnet_cidr_block
  }
}

resource "azurerm_public_ip" "primary_public_ip" {
  name                = "primary_public_ip"
  location            = azurerm_resource_group.azure_rg.location
  resource_group_name = azurerm_resource_group.azure_rg.name

  allocation_method = "Dynamic"
}

resource "azurerm_public_ip" "secondary_public_ip" {
  name                = "secondary_public_ip"
  location            = azurerm_resource_group.azure_rg.location
  resource_group_name = azurerm_resource_group.azure_rg.name

  allocation_method = "Dynamic"
}

resource "azurerm_virtual_network_gateway" "azure_vpn_gateway" {
  name                = "azure_vpn_gateway"
  location            = azurerm_resource_group.azure_rg.location
  resource_group_name = azurerm_resource_group.azure_rg.name

  type     = "Vpn"
  vpn_type = "RouteBased"

  active_active = true
  enable_bgp    = true
  sku           = var.azure_vpn_gateway_sku
  generation = var.azure_vpn_gateway_generation

  default_local_network_gateway_id = var.azure_gateway_subnet_cidr_block
  
  ip_configuration {
    name = var.azure_vpn_gateway_public_ip_name
    subnet_id = var.azure_gateway_subnet_cidr_block
    public_ip_address_id = azurerm_public_ip.primary_public_ip.id
  }

  ip_configuration {
    name = var.azure_vpn_gateway_secondary_ip_name
    subnet_id = var.azure_gateway_subnet_cidr_block
    public_ip_address_id = azurerm_public_ip.secondary_public_ip.id
  }

  bgp_settings {
    asn = var.azure_bgp_asn
    peering_addresses {
      ip_configuration_name = var.azure_vpn_gateway_primary_ip_name
      apipa_addresses = var.apipa_addresses_primary
    }

    peering_addresses {
      ip_configuration_name = var.azure_vpn_gateway_secondary_ip_name
      apipa_addresses = var.apipa_addresses_secondary
    }
  }
}

resource "azurerm_local_network_gateway" "local_gateway_1" {
  name                = "local_gateway_1"
  resource_group_name = azurerm_resource_group.azure_rg.name
  location            = azurerm_resource_group.azure_rg.location
  
  depends_on = [
    aws_vpn_connection
  ]

  gateway_address = aws_vpn_connection.aws_site_vpn.tunnel1_cgw_inside_address

  bgp_settings {
    asn = var.aws_asn
    bgp_peering_address = var.local_gateway_1_bgp_peer
  }
}

resource "azurerm_virtual_network_gateway_connection" "connection_1" {
  name                = "connection_to_tunnel1"
  location            = azurerm_resource_group.azure_rg.location
  resource_group_name = azurerm_resource_group.azure_rg.name

  type                       = "IPsec"
  virtual_network_gateway_id = azurerm_virtual_network_gateway.azure_vpn_gateway.id
  local_network_gateway_id   = azurerm_local_network_gateway.local_gateway_1.id

  shared_key = aws_vpn_connection.aws_site_vpn.tunnel1_preshared_key
}