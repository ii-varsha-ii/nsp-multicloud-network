provider "aws" {
  region = var.aws_region
}

# -----------------------------------------------------------------------------------------------
# VPC and Subnets
# -----------------------------------------------------------------------------------------------

resource "aws_vpc" "aws_vpc_1" {
  cidr_block = var.vpc_1_cidr_block
  tags = {
    "Name" = var.vpc_name_tag
  }
  enable_dns_support = true
  enable_dns_hostnames = true
}

resource "aws_subnet" "public_subnet" {
  vpc_id = aws_vpc.aws_vpc_1.id
  cidr_block = var.public_subnet_cidr

  tags = {
    "Name": var.public_subnet_name_tag
  }
}

resource "aws_subnet" "private_subnet" {
  vpc_id = aws_vpc.aws_vpc_1.id
  cidr_block = var.private_subnet_cidr

  tags = {
    "Name": var.private_subnet_name_tag
  }
}

# -----------------------------------------------------------------------------------------------
# Internet Gateway
# -----------------------------------------------------------------------------------------------

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.aws_vpc_1.id

  tags = {
    Name = "IGW"
  }
}

# -----------------------------------------------------------------------------------------------
# Create public and private route tables and associate it with public and private subnet
# -----------------------------------------------------------------------------------------------

resource "aws_route_table" "public_subnet_route_table" {
  vpc_id = aws_vpc.aws_vpc_1.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }

  tags = {
    Name = "public_subnet_route_table"
  }
}

resource "aws_route_table" "private_subnet_route_table" {
  vpc_id = aws_vpc.aws_vpc_1.id

  tags = {
    Name = "private_subnet_route_table"
  }
}

resource "aws_route_table_association" "public_subnet_association" {
  subnet_id      = aws_subnet.public_subnet.id
  route_table_id = aws_route_table.public_subnet_route_table.id
}

resource "aws_route_table_association" "private_subnet_association" {
  subnet_id      = aws_subnet.private_subnet.id
  route_table_id = aws_route_table.private_subnet_route_table.id
}

# -----------------------------------------------------------------------------------------------
# Transit Gateways and Transit Gateway attachments
# -----------------------------------------------------------------------------------------------

resource "aws_ec2_transit_gateway" "tgw" {
  description = "Transit gateway"
  amazon_side_asn = var.aws_asn
  tags = {
    "Name" = "TGW"
  }
}

resource "aws_ec2_transit_gateway_vpc_attachment" "tgw_attachment_to_vpc" {
  subnet_ids         = [aws_subnet.private_subnet.id]
  transit_gateway_id = aws_ec2_transit_gateway.tgw.id
  vpc_id             = aws_vpc.aws_vpc_1.id
  tags = {
    "Name" = "Transit gateway VPC attachment"
  }
}

# FINISH AZURE HERE


# Add a route to the VPC to the TGW to the AZURE destination cidr block 

resource "aws_route" "vpc_to_tgw_route" {
  route_table_id = aws_route_table.private_subnet_route_table.id
  transit_gateway_id = aws_ec2_transit_gateway.tgw.id
  destination_cidr_block = var.azure_vpc_cidr_block
}

# -----------------------------------------------------------------------------------------------
# Customer Gateway
# -----------------------------------------------------------------------------------------------

resource "aws_customer_gateway" "customer_gateway_to_azure" {
  bgp_asn    = var.azure_bgp_asn
  ip_address = azurerm_public_ip.primary_public_ip.ip_address     # depends on azure vpn
  type       = "ipsec.1"
}

# -----------------------------------------------------------------------------------------------
# AWS VPN connection connecting to the TGW
# -----------------------------------------------------------------------------------------------

resource "aws_vpn_connection" "aws_site_vpn" {
  customer_gateway_id = aws_customer_gateway.customer_gateway_to_azure.id
  transit_gateway_id  = aws_ec2_transit_gateway.tgw.id
  type                = aws_customer_gateway.customer_gateway_to_azure.type
  tunnel1_inside_cidr = var.tunnel1_inside_cidr
  tunnel2_inside_cidr = var.tunnel2_inside_cidr
  tunnel1_ike_versions = var.ike_version
  tunnel2_ike_versions = var.ike_version
  tunnel1_startup_action = var.tunnel_startup_action

  tags = {
    Name = "Transit Gateway VPN Connection"
  }
}

# Add a route in the TGW routing table to the attachment
resource "aws_route" "tgw_to_vpn_route" {
  route_table_id = aws_ec2_transit_gateway.tgw.association_default_route_table_id
  transit_gateway_id = aws_ec2_transit_gateway.tgw.transit_gateway_attachment_id
  destination_cidr_block = var.azure_vpc_cidr_block
}


# -----------------------------------------------------------------------------------------------
# Create Public and Private EC2 instances
# -----------------------------------------------------------------------------------------------

resource "tls_private_key" "private_key" {
  algorithm = "RSA"
  rsa_bits  = 4096
}
resource "aws_key_pair" "generated_key" {
  key_name   = "ec2key"
  public_key = tls_private_key.example.public_key_openssh
}

resource "aws_network_interface" "public_subnet_network_interface" {
  subnet_id   = aws_subnet.public_subnet.id
  tags = {
    Name = "public_subnet_network_interface"
  }
}

resource "aws_network_interface" "private_subnet_network_interface" {
  subnet_id   = aws_subnet.private_subnet.id
  tags = {
    Name = "private_subnet_network_interface"
  }
}

resource "aws_security_group" "default_security_group" {
  name        = "default_security_group"
  description = "Default Security Group which enables ICMP traffic"
  vpc_id      = aws_vpc.aws_vpc_1.id

  ingress {
    description      = "TCP 22"
    from_port        = 22
    to_port          = 22
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
  }

  ingress {
    from_port        = -1
    to_port          = -1
    protocol         = "icmp"
    cidr_blocks      = ["0.0.0.0/0"]
  }

  tags = {
    Name = "default_security_group"
  }
}

resource "aws_instance" "public_instance_1" {
  ami           = "ami-065bb5126e4504910"
  instance_type = "t2.micro"
  key_name = aws_key_pair.generated_key.key_name

  associate_public_ip_address = true
  
  security_groups  = [aws_security_group.default_security_group.id]

  network_interface {
    network_interface_id = aws_network_interface.public_subnet_network_interface.id
    device_index         = 0
  }

  tags = {
    Name = "public_instance_1"
  }
}

resource "aws_instance" "private_instance_1" {
  ami           = "ami-065bb5126e4504910"
  instance_type = "t2.micro"
  key_name = aws_key_pair.generated_key.key_name

  associate_public_ip_address = true
  
  security_groups  = [aws_security_group.default_security_group.id]

  network_interface {
    network_interface_id = aws_network_interface.private_subnet_network_interface.id
    device_index         = 0
  }

  tags = {
    Name = "private_instance_1"
  }
}