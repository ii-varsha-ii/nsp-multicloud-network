import logging
import time

import boto3
from botocore.exceptions import ClientError

from services.ec2 import delete_security_group, delete_ec2
from services.transit_gateways import delete_transit_gateway_vpc_attachments, delete_transit_gateway, \
    delete_transit_gateway_peering_attachments
from services.vpc import delete_subnet, delete_vpc, delete_igw, delete_route_table
from utils.utils import load_config, fetch_constants


def _cleanup_vpc(client, vpc_id):
    delete_vpc(client, vpc_id)


def _cleanup_routing_table(client, rt_id):
    delete_route_table(client, rt_id)


def _cleanup_igw(client, igw_id, vpc_id):
    delete_igw(client, igw_id, vpc_id)


def _cleanup_subnets(client, subnet_id):
    delete_subnet(client, subnet_id)


def _cleanup_transit_gateway_vpc_attachments(client, tgw_id):
    delete_transit_gateway_vpc_attachments(client, tgw_id)


def _cleanup_transit_gateway_peering_attachments(client, tgw_id):
    delete_transit_gateway_peering_attachments(client, tgw_id)


def _cleanup_transit_gateway(client, tgw_id):
    delete_transit_gateway(client, tgw_id)


def _cleanup_security_groups(client, sg_id):
    delete_security_group(client, sg_id)


def _cleanup_ec2(client, instance_id):
    delete_ec2(client, instance_id)


def cleanup_intra_region(section: str, us_east_1_client):
    actual_values: dict = load_config(filename=section)
    constants = fetch_constants(section=section)
    try:
        _cleanup_ec2(us_east_1_client, actual_values[constants['EC2_PUB_1_VPC1']])
        _cleanup_ec2(us_east_1_client, actual_values[constants['EC2_PRI_2_VPC1']])
        _cleanup_ec2(us_east_1_client, actual_values[constants['EC2_PRI_1_VPC2']])

        _cleanup_transit_gateway_vpc_attachments(us_east_1_client, actual_values[constants['TGW_ATTACH_VPC1']])
        _cleanup_transit_gateway_vpc_attachments(us_east_1_client, actual_values[constants['TGW_ATTACH_VPC2']])

        time.sleep(100)

        _cleanup_transit_gateway(us_east_1_client, actual_values[constants['TGW_1']])
        _cleanup_transit_gateway(us_east_1_client, actual_values[constants['TGW_2']])

        time.sleep(100)

        _cleanup_subnets(us_east_1_client, actual_values[constants['SUBNET1_VPC1']])
        _cleanup_subnets(us_east_1_client, actual_values[constants['SUBNET2_VPC1']])
        _cleanup_subnets(us_east_1_client, actual_values[constants['SUBNET1_VPC2']])

        _cleanup_security_groups(us_east_1_client, actual_values[constants['SG_PUB_1_VPC1']])
        _cleanup_security_groups(us_east_1_client, actual_values[constants['SG_PRI_2_VPC1']])
        _cleanup_security_groups(us_east_1_client, actual_values[constants['SG_PRI_1_VPC2']])

        _cleanup_igw(us_east_1_client, actual_values[constants['IGW']], actual_values[constants['VPC1']])
        _cleanup_routing_table(us_east_1_client, actual_values[constants['VPC1_PRI_ROUTE_TABLE']])

        _cleanup_vpc(us_east_1_client, actual_values[constants['VPC1']])
        _cleanup_vpc(us_east_1_client, actual_values[constants['VPC2']])

    except ClientError as e:
        logging.exception(f'Nevermind - {e}')


def cleanup_inter_region(section, us_east_1_client, us_west_1_client):
    actual_values: dict = load_config(filename=section)
    constants = fetch_constants(section=section)
    try:
        _cleanup_ec2(us_east_1_client, actual_values[constants['EC2_PUB_1_VPC1']])
        _cleanup_ec2(us_east_1_client, actual_values[constants['EC2_PRI_2_VPC1']])
        _cleanup_ec2(us_west_1_client, actual_values[constants['EC2_PRI_1_VPC2']])

        _cleanup_transit_gateway_vpc_attachments(us_east_1_client, actual_values[constants['TGW_ATTACH_VPC1']])
        _cleanup_transit_gateway_vpc_attachments(us_east_1_client, actual_values[constants['TGW_ATTACH_VPC2']])
        _cleanup_transit_gateway_peering_attachments(us_west_1_client, actual_values[constants['TGW_PEER_CONNECT']])

        time.sleep(100)

        _cleanup_transit_gateway(us_east_1_client, actual_values[constants['TGW_1']])
        _cleanup_transit_gateway(us_west_1_client, actual_values[constants['TGW_2']])

        time.sleep(100)

        _cleanup_subnets(us_east_1_client, actual_values[constants['SUBNET1_VPC1']])
        _cleanup_subnets(us_east_1_client, actual_values[constants['SUBNET2_VPC1']])
        _cleanup_subnets(us_west_1_client, actual_values[constants['SUBNET1_VPC2']])

        _cleanup_security_groups(us_east_1_client, actual_values[constants['SG_PUB_1_VPC1']])
        _cleanup_security_groups(us_east_1_client, actual_values[constants['SG_PRI_2_VPC1']])
        _cleanup_security_groups(us_west_1_client, actual_values[constants['SG_PRI_1_VPC2']])

        _cleanup_igw(us_east_1_client, actual_values[constants['IGW']], actual_values[constants['VPC1']])
        _cleanup_routing_table(us_east_1_client, actual_values[constants['VPC1_PRI_ROUTE_TABLE']])

        _cleanup_vpc(us_east_1_client, actual_values[constants['VPC1']])
        _cleanup_vpc(us_west_1_client, actual_values[constants['VPC2']])

    except ClientError as e:
        logging.exception(f'Nevermind - {e}')


if __name__ == '__main__':
    us_east_1_resource = boto3.resource('ec2', region_name='us-east-1')
    us_west_1_resource = boto3.resource('ec2', region_name='us-west-1')

    us_east_1_client = boto3.client('ec2', region_name='us-east-1')
    us_west_1_client = boto3.client('ec2', region_name='us-west-1')

    cleanup_intra_region(section='inter_region', us_east_1_client=us_east_1_client)
    cleanup_inter_region(section='inter_region', us_east_1_client=us_east_1_client, us_west_1_client=us_west_1_client)
