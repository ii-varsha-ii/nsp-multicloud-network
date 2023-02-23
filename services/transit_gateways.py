import logging
import random
import time

import boto3
from botocore.exceptions import ClientError

from utils.utils import store_config, load_config

logger = logging.getLogger()
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s: %(levelname)s: %(message)s')

account_id = "337332556540"


def create_transit_gateway(client, tgw_name: str, tgw_route_table: str, filename: str, persist: bool):
    try:
        tg = client.create_transit_gateway(
            Description="Automated Transit gateway created to connect VPCs",
            Options={
                'AmazonSideAsn': random.randrange(64512, 65534),
            }
        )
        if persist:
            store_config(value=tg['TransitGateway']['TransitGatewayId'], key=tgw_name, filename=filename)
            store_config(value=tg['TransitGateway']['Options']['AssociationDefaultRouteTableId'], key=tgw_route_table,
                         filename=filename)
        logger.info(f'Transit gateway created : {tg}')
    except ClientError as e:
        logger.exception('Could not create transit gateway', e)
    else:
        return tg


def delete_transit_gateway(client, tgw_id):
    try:
        response = client.delete_transit_gateway(TransitGatewayId=tgw_id)
    except ClientError as e:
        logger.exception('Could not delete transit gateway', e)
    else:
        return response


def delete_transit_gateway_vpc_attachments(client, tgw_attach_id):
    try:
        response = client.delete_transit_gateway_vpc_attachment(TransitGatewayAttachmentId=tgw_attach_id)
    except ClientError as e:
        logger.exception('Could not delete transit gateway attachment', e)
    else:
        return response


def delete_transit_gateway_peering_attachments(client, tgw_peer_id):
    try:
        response = client.delete_transit_gateway_peering_attachment(TransitGatewayAttachmentId=tgw_peer_id)
    except ClientError as e:
        logger.exception('Could not delete transit gateway peering attachment', e)
    else:
        return response


def create_transit_gateway_attachments(client, tgw_attachment_name: str, tgw: str, vpc: str, subnet: str, filename: str,
                                       persist: bool):
    try:
        tgw_id = load_config(filename=filename, key=tgw)
        vpc_id = load_config(filename=filename, key=vpc)
        subnet_id = load_config(filename=filename, key=subnet)
        tga = client.create_transit_gateway_vpc_attachment(
            TransitGatewayId=tgw_id,
            VpcId=vpc_id,
            SubnetIds=[subnet_id],
            TagSpecifications=[
                {
                    'ResourceType': 'transit-gateway-attachment',
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value': tgw_attachment_name
                        },
                    ]
                },
            ]
        )
        if persist:
            store_config(value=tga['TransitGatewayVpcAttachment']['TransitGatewayAttachmentId'],
                         key=tgw_attachment_name, filename=filename)
    except ClientError as e:
        logger.exception('Could not create transit gateway attachment', e)


def create_transit_gateway_peering_connection(client,
                                              tgw_peer_name: str,
                                              tgw_1: str,
                                              tgw_2: str,
                                              tgw_2_region: str,
                                              filename: str,
                                              persist: bool):
    try:
        tgw_1_id = load_config(filename=filename, key=tgw_1)
        tgw_2_id = load_config(filename=filename, key=tgw_2)
        tga = client.create_transit_gateway_peering_attachment(
            TransitGatewayId=tgw_1_id,
            PeerTransitGatewayId=tgw_2_id,
            PeerAccountId=account_id,
            PeerRegion=tgw_2_region,
            TagSpecifications=[
                {
                    'ResourceType': 'transit-gateway-attachment',
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value': tgw_peer_name
                        },
                    ]
                },
            ]
        )
        if persist:
            store_config(value=tga['TransitGatewayPeeringAttachment']['TransitGatewayAttachmentId'],
                         key=tgw_peer_name, filename=filename)
    except ClientError as e:
        logger.exception('Could not create transit gateway attachment', e)
    else:
        return tga


def describe_transit_gateway_attachment(client,
                                        tgw_peer_name: str,
                                        filename: str,
                                        persist: bool):
    tgw_peer_attachment = load_config(filename=filename, key=tgw_peer_name)
    try:
        desc = client.describe_transit_gateway_attachments(TransitGatewayAttachmentIds=[tgw_peer_attachment])
    except ClientError as e:
        logger.exception('Could not create transit gateway attachment', e)
    else:
        return desc


def accept_tgw_peering_connection(client,
                                  tgw_peer_connect: str,
                                  filename: str,
                                  persist: bool):
    try:
        tgw_peer_id = load_config(filename=filename, key=tgw_peer_connect)
        response = client.accept_transit_gateway_peering_attachment(
            TransitGatewayAttachmentId=tgw_peer_id
        )
    except ClientError as e:
        logger.exception('Could not create transit gateway attachment', e)
    else:
        return response


def create_tgw_route_with_peering_attachment(client,
                                             tgw_route_table: str,
                                             vpc_network: str,
                                             tgw_peer_connect: str,
                                             filename: str):
    try:
        tgw_peer_id = load_config(filename=filename, key=tgw_peer_connect)
        tgw_rt_id = load_config(filename=filename, key=tgw_route_table)
        response = client.create_transit_gateway_route(
            DestinationCidrBlock=vpc_network,
            TransitGatewayRouteTableId=tgw_rt_id,
            TransitGatewayAttachmentId=tgw_peer_id
        )
    except ClientError as e:
        logger.exception(f'Could not create route with tgw peering', e)
    else:
        return response


def create_route_with_tgw(client, tgw: str, vpc_network: str, route_table: str, filename: str):
    try:
        tgw_id = load_config(filename=filename, key=tgw)
        route_table_id = load_config(filename=filename, key=route_table)
        route_table_client = client.RouteTable(route_table_id)
        response = route_table_client.create_route(DestinationCidrBlock=vpc_network, TransitGatewayId=tgw_id)
        logger.info(f'Route created with {tgw_id} and {vpc_network} in {route_table_id}')
    except ClientError as e:
        logger.exception(f'Could not create route with tgw', e)
