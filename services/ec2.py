import logging

import boto3
from botocore.exceptions import ClientError

from utils.utils import store_config, load_config

client = boto3.resource('ec2')
ec2client = client.meta.client

logger = logging.getLogger()
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s: %(levelname)s: %(message)s')


def delete_security_group(group_id):
    try:
        response = ec2client.delete_security_group(GroupId=group_id)
    except ClientError as e:
        logger.exception('Could not delete security group')
    else:
        return response


def create_security_group(group_name: str, ec2_name: str, vpc: str, filename: str, persist: bool):
    try:
        vpc_id = load_config(filename=filename, key=vpc)
        security_group = ec2client.create_security_group(Description=f'Automated Security Group created for {ec2_name}',
                                                         GroupName=group_name,
                                                         VpcId=vpc_id,
                                                         TagSpecifications=[
                                                             {
                                                                 'ResourceType': 'security-group',
                                                                 'Tags': [
                                                                     {
                                                                         'Key': "Name",
                                                                         'Value': group_name
                                                                     },
                                                                 ]
                                                             },
                                                         ]
                                                         )
        if persist:
            store_config(value=security_group['GroupId'],
                         key=group_name, filename=filename)

        logger.info(f'Security Group created: {security_group}')
        security_group_rules = ec2client.authorize_security_group_ingress(
            GroupId=security_group['GroupId'],
            IpPermissions=[
                {'IpProtocol': 'tcp',
                 'FromPort': 22,
                 'ToPort': 22,
                 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
                {'IpProtocol': 'icmp',
                 'FromPort': -1,
                 'ToPort': -1,
                 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
            ])
        logger.info(f'Security Group Rules updated: {security_group_rules}')

    except ClientError as e:
        logger.exception('Could not create security group', e)
    else:
        return security_group


def create_ec2(ec2_name: str, subnet: str, security_group: str, enable_public_ip: bool, filename: str, persist: bool):
    # defaulted hence hardcoded
    image_id = 'ami-065bb5126e4504910'
    key_pair = 'defaultvpc_instance1'
    min_count = 1
    max_count = 1
    instance_type = 't2.micro'
    subnet_id = load_config(filename=filename, key=subnet)
    security_group_id = load_config(filename=filename, key=security_group)
    instances = client.create_instances(
        ImageId=image_id,
        MinCount=min_count,
        MaxCount=max_count,
        InstanceType=instance_type,
        KeyName=key_pair,
        NetworkInterfaces=[
            {
                'DeviceIndex': 0,
                'SubnetId': subnet_id,
                'Groups': [security_group_id],
                'AssociatePublicIpAddress': enable_public_ip
            }
        ],
        TagSpecifications=[
            {
                'ResourceType': 'instance',
                'Tags': [
                    {
                        'Key': 'Name',
                        'Value': ec2_name
                    },
                ]
            },
        ],
    )
    logger.info(instances)
    if persist:
        pass
    return instances


if __name__ == '__main__':
    pass
