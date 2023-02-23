import logging
import time

import boto3

from services.ec2 import create_security_group, create_ec2
from services.transit_gateways import create_transit_gateway, create_transit_gateway_attachments, create_route_with_tgw, \
    create_transit_gateway_peering_connection, accept_tgw_peering_connection, describe_transit_gateway_attachment, \
    create_tgw_route_with_peering_attachment
from services.vpc import create_vpc, create_subnet, create_internet_gateways, attach_vpc_with_ig, \
    find_existing_route_tables, create_route_with_igw, create_routing_table_associate
from utils.utils import fetch_constants

logger = logging.getLogger()
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s: %(levelname)s: %(message)s')

us_east_1_resource = boto3.resource('ec2', region_name='us-east-1')
us_west_1_resource = boto3.resource('ec2', region_name='us-west-1')

us_east_1_client = boto3.client('ec2', region_name='us-east-1')
us_west_1_client = boto3.client('ec2', region_name='us-west-1')


def create_vpcs(section, constants):
    IP_CIDR1 = constants['IP_CIDR1']
    IP_CIDR2 = constants['IP_CIDR2']
    VPC1 = constants['VPC1']
    VPC2 = constants['VPC2']

    SUBNET_CIDR11 = constants['SUBNET_CIDR11']
    SUBNET_CIDR12 = constants['SUBNET_CIDR12']
    SUBNET_CIDR21 = constants['SUBNET_CIDR21']
    SUBNET1_VPC1 = constants['SUBNET1_VPC1']
    SUBNET2_VPC1 = constants['SUBNET2_VPC1']
    SUBNET1_VPC2 = constants['SUBNET1_VPC2']

    REGION1_AZ = constants['REGION1_AZ']
    REGION2_AZ = constants['REGION2_AZ']

    IGW = constants['IGW']

    VPC1_PUB_ROUTE_TABLE = constants['VPC1_PUB_ROUTE_TABLE']
    VPC2_PRI_ROUTE_TABLE = constants['VPC2_PRI_ROUTE_TABLE']
    VPC1_PRI_ROUTE_TABLE = constants['VPC1_PRI_ROUTE_TABLE']
    vpc_1 = create_vpc(resource=us_east_1_resource, name=VPC1, ip_cidr=IP_CIDR1, filename=section, persist=True)
    vpc_2 = create_vpc(resource=us_west_1_resource, name=VPC2, ip_cidr=IP_CIDR2, filename=section, persist=True)

    logger.info('Creating Subnets:')
    subnet1_vpc_1 = create_subnet(resource=us_east_1_resource, subnet_name=SUBNET1_VPC1, subnet_ip_cidr=SUBNET_CIDR11,
                                  vpc_name=VPC1,
                                  az=REGION1_AZ,
                                  filename=section, persist=True)
    subnet2_vpc_1 = create_subnet(resource=us_east_1_resource, subnet_name=SUBNET2_VPC1, subnet_ip_cidr=SUBNET_CIDR12,
                                  vpc_name=VPC1,
                                  az=REGION1_AZ,
                                  filename=section, persist=True)
    subnet1_vpc_2 = create_subnet(resource=us_west_1_resource, subnet_name=SUBNET1_VPC2, subnet_ip_cidr=SUBNET_CIDR21,
                                  vpc_name=VPC2,
                                  az=REGION2_AZ,
                                  filename=section, persist=True)

    logger.info('Creating Internet Gateway')
    ig = create_internet_gateways(resource=us_east_1_resource, ig_name=IGW, filename=section, persist=True)
    attach_vpc_with_ig(resource=us_east_1_resource, vpc=VPC1, igw=IGW, filename=section)

    find_existing_route_tables(resource=us_east_1_resource, route_table_name=VPC1_PUB_ROUTE_TABLE, vpc=VPC1,
                               filename=section,
                               persist=True)
    find_existing_route_tables(resource=us_west_1_resource, route_table_name=VPC2_PRI_ROUTE_TABLE, vpc=VPC2,
                               filename=section,
                               persist=True)

    create_route_with_igw(resource=us_east_1_resource, igw=IGW, route_table=VPC1_PUB_ROUTE_TABLE,
                          destination_ip_cidr='0.0.0.0/0',
                          filename=section)

    logger.info('Creating private routing table')
    private_route_table_vpc_1 = create_routing_table_associate(resource=us_east_1_resource,
                                                               route_table_name=VPC1_PRI_ROUTE_TABLE,
                                                               vpc=VPC1,
                                                               subnet=SUBNET2_VPC1,
                                                               filename=section,
                                                               persist=True)


def create_tgw(section, constants):
    TGW_1 = constants['TGW_1']
    TGW_2 = constants['TGW_2']
    REGION1 = constants['REGION1']
    REGION2 = constants['REGION2']
    TGW_PEER_CONNECT = constants['TGW_PEER_CONNECT']
    TGW_ATTACH_VPC1 = constants['TGW_ATTACH_VPC1']
    TGW_ATTACH_VPC2 = constants['TGW_ATTACH_VPC2']

    IP_CIDR1 = constants['IP_CIDR1']
    IP_CIDR2 = constants['IP_CIDR2']
    VPC1 = constants['VPC1']
    VPC2 = constants['VPC2']

    SUBNET1_VPC1 = constants['SUBNET1_VPC1']
    SUBNET2_VPC1 = constants['SUBNET2_VPC1']
    SUBNET1_VPC2 = constants['SUBNET1_VPC2']

    TGW_1_ROUTE_TABLE = constants['TGW_1_ROUTE_TABLE']
    TGW_2_ROUTE_TABLE = constants['TGW_2_ROUTE_TABLE']

    VPC2_PRI_ROUTE_TABLE = constants['VPC2_PRI_ROUTE_TABLE']
    VPC1_PRI_ROUTE_TABLE = constants['VPC1_PRI_ROUTE_TABLE']

    create_transit_gateway(client=us_east_1_client, tgw_name=TGW_1, tgw_route_table=TGW_1_ROUTE_TABLE, filename=section,
                           persist=True)
    create_transit_gateway(client=us_west_1_client, tgw_name=TGW_2, tgw_route_table=TGW_2_ROUTE_TABLE, filename=section,
                           persist=True)
    time.sleep(20)

    tga = create_transit_gateway_peering_connection(client=us_east_1_client,
                                                    tgw_peer_name=TGW_PEER_CONNECT,
                                                    tgw_1=TGW_1, tgw_2=TGW_2,
                                                    tgw_2_region=REGION2, filename=section, persist=True)

    while True:
        desc = describe_transit_gateway_attachment(client=us_east_1_client,
                                                   tgw_peer_name=TGW_PEER_CONNECT,
                                                   filename=section, persist=True)
        if desc['TransitGatewayAttachments'][0]['State'] == 'pendingAcceptance':
            break
        time.sleep(10)

    accept_tgw_peering_connection(client=us_west_1_client, tgw_peer_connect=TGW_PEER_CONNECT, filename=section,
                                  persist=True)
    while True:
        desc = describe_transit_gateway_attachment(client=us_west_1_client,
                                                   tgw_peer_name=TGW_PEER_CONNECT,
                                                   filename=section, persist=True)
        if desc['TransitGatewayAttachments'][0]['State'] == 'available':
            break
        time.sleep(10)

    create_transit_gateway_attachments(client=us_east_1_client, tgw_attachment_name=TGW_ATTACH_VPC1,
                                       tgw=TGW_1, vpc=VPC1, subnet=SUBNET2_VPC1, filename=section, persist=True)
    create_transit_gateway_attachments(client=us_west_1_client, tgw_attachment_name=TGW_ATTACH_VPC2,
                                       tgw=TGW_2, vpc=VPC2, subnet=SUBNET1_VPC2, filename=section, persist=True)

    create_route_with_tgw(client=us_east_1_resource, tgw=TGW_1, vpc_network=IP_CIDR2, route_table=VPC1_PRI_ROUTE_TABLE,
                          filename=section)
    create_route_with_tgw(client=us_west_1_resource, tgw=TGW_2, vpc_network=IP_CIDR1, route_table=VPC2_PRI_ROUTE_TABLE,
                          filename=section)

    create_tgw_route_with_peering_attachment(client=us_east_1_client, tgw_route_table=TGW_1_ROUTE_TABLE, vpc_network=IP_CIDR2,
                                             tgw_peer_connect=TGW_PEER_CONNECT, filename=section)

    create_tgw_route_with_peering_attachment(client=us_west_1_client, tgw_route_table=TGW_2_ROUTE_TABLE, vpc_network=IP_CIDR1,
                                             tgw_peer_connect=TGW_PEER_CONNECT, filename=section)


def create_vms(section, constants):
    VPC1 = constants['VPC1']
    VPC2 = constants['VPC2']

    SUBNET1_VPC1 = constants['SUBNET1_VPC1']
    SUBNET2_VPC1 = constants['SUBNET2_VPC1']
    SUBNET1_VPC2 = constants['SUBNET1_VPC2']

    EC2_PUB_1_VPC1 = constants['EC2_PUB_1_VPC1']
    EC2_PRI_2_VPC1 = constants['EC2_PRI_2_VPC1']
    EC2_PRI_1_VPC2 = constants['EC2_PRI_1_VPC2']

    US_EAST_1_IMAGE = constants['US_EAST_1_IMAGE']
    US_WEST_1_IMAGE = constants['US_WEST_1_IMAGE']

    SG_PUB_1_VPC1 = constants['SG_PUB_1_VPC1']
    SG_PRI_2_VPC1 = constants['SG_PRI_2_VPC1']
    SG_PRI_1_VPC2 = constants['SG_PRI_1_VPC2']

    create_security_group(client=us_east_1_client, group_name=SG_PUB_1_VPC1, ec2_name=EC2_PUB_1_VPC1, vpc=VPC1,
                          filename=section,
                          persist=True)
    create_security_group(client=us_east_1_client, group_name=SG_PRI_2_VPC1, ec2_name=EC2_PRI_2_VPC1, vpc=VPC1,
                          filename=section,
                          persist=True)
    create_security_group(client=us_west_1_client, group_name=SG_PRI_1_VPC2, ec2_name=EC2_PRI_1_VPC2, vpc=VPC2,
                          filename=section,
                          persist=True)

    create_ec2(client=us_east_1_resource,
               ec2_name=EC2_PUB_1_VPC1, subnet=SUBNET1_VPC1, security_group=SG_PUB_1_VPC1, keypair='defaultvpc_instance1',enable_public_ip=True,
               image=US_EAST_1_IMAGE,
               filename=section,
               persist=True)
    create_ec2(client=us_east_1_resource,
               ec2_name=EC2_PRI_2_VPC1, subnet=SUBNET2_VPC1, security_group=SG_PRI_2_VPC1, keypair='defaultvpc_instance1', enable_public_ip=False,
               image=US_EAST_1_IMAGE,
               filename=section,
               persist=True)
    create_ec2(client=us_west_1_resource,
               ec2_name=EC2_PRI_1_VPC2, subnet=SUBNET1_VPC2, security_group=SG_PRI_1_VPC2, keypair=None, enable_public_ip=False,
               image=US_WEST_1_IMAGE,
               filename=section,
               persist=True)


def run_inter_region():
    section = 'inter_region'
    constants = fetch_constants(section=section)

    logger.info('Creating VPCs:')
    create_vpcs(section, constants)
    logger.info('Created VPCs, subnets, IG, Routes, and Routing tables. Continue?')
    key = input('Press Y key to continue. N to stop')

    if key == 'N':
        return

    logger.info('Starting TGW creation')
    create_tgw(section, constants)
    logger.info('Created Transit Gateways, attachments and routes. Continue?')
    key = input('Press Y key to continue. N to stop')

    if key == 'N':
        return

    logger.info('Starting EC2 and rules creation')
    create_vms(section, constants)
    logger.info('Created EC2 and routes. Go ahead and test it out')


if __name__ == '__main__':
    run_inter_region()
