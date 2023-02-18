import logging
import random
import time

import boto3
from botocore.exceptions import ClientError

from utils.utils import store_config, load_config

client = boto3.resource('ec2')
ec2client = client.meta.client

logger = logging.getLogger()
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s: %(levelname)s: %(message)s')


def create_transit_gateway(tgw_name: str, filename: str, persist: bool):
    try:
        tg = ec2client.create_transit_gateway(
            Description="Automated Transit gateway created to connect VPCs",
            Options={
                'AmazonSideAsn': random.randrange(64512, 65534),
            }
        )
        if persist:
            store_config(value=tg['TransitGateway']['TransitGatewayId'], key=tgw_name, filename=filename)
        logger.info(f'Transit gateway created : {tg}')
    except ClientError as e:
        logger.exception('Could not create transit gateway', e)
    else:
        return tg


def delete_transit_gateway(tgw_id):
    try:
        response = ec2client.delete_transit_gateway(TransitGatewayId=tgw_id)
    except ClientError as e:
        logger.exception('Could not delete transit gateway', e)
    else:
        return response


def delete_transit_gateway_attachments(tgw_attach_vpc1_id):
    try:
        response = ec2client.delete_transit_gateway_vpc_attachment(TransitGatewayAttachmentId=tgw_attach_vpc1_id)
    except ClientError as e:
        logger.exception('Could not delete transit gateway attachment', e)
    else:
        return response


def create_transit_gateway_attachments(tgw_attachment_name: str, tgw: str, vpc: str, subnet: str, filename: str,
                                       persist: bool):
    try:
        tgw_id = load_config(filename=filename, key=tgw)
        vpc_id = load_config(filename=filename, key=vpc)
        subnet_id = load_config(filename=filename, key=subnet)
        tga = ec2client.create_transit_gateway_vpc_attachment(
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


def create_route_with_tgw(tgw: str, vpc_network: str, route_table: str, filename: str):
    try:
        tgw_id = load_config(filename=filename, key=tgw)
        route_table_id = load_config(filename=filename, key=route_table)
        response = ec2client.create_route(DestinationCidrBlock=vpc_network, TransitGatewayId=tgw_id,
                                          RouteTableId=route_table_id)
        logger.info(f'Route created with {tgw_id} and {vpc_network} in {route_table_id}')
    except ClientError as e:
        logger.exception(f'Could not create route with tgw', e)


if __name__ == '__main__':
    pass