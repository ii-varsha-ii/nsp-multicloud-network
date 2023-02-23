import logging
from typing import Optional

import boto3
from botocore.exceptions import ClientError

from utils.utils import store_config, load_config

client = boto3.resource('ec2')
ec2client = client.meta.client

logger = logging.getLogger()
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s: %(levelname)s: %(message)s')


def delete_security_group(client, group_id):
    try:
        response = client.delete_security_group(GroupId=group_id)
    except ClientError as e:
        logger.exception('Could not delete security group')
    else:
        return response


def delete_ec2(client, instance_id):
    try:
        response = client.terminate_instances(InstanceIds=[instance_id])
    except ClientError as e:
        logger.exception(f'Could not delete instance {instance_id}')
    else:
        return response


def create_security_group(client, group_name: str, ec2_name: str, vpc: str, filename: str, persist: bool):
    try:
        vpc_id = load_config(filename=filename, key=vpc)
        security_group = client.create_security_group(Description=f'Automated Security Group created for {ec2_name}',
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
        security_group_rules = client.authorize_security_group_ingress(
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


def create_ec2(client, ec2_name: str, subnet: str, security_group: str, keypair: Optional[str], enable_public_ip: bool, image: str,
               filename: str, persist: bool):
    # defaulted hence hardcoded
    min_count = 1
    max_count = 1
    instance_type = 't2.micro'
    subnet_id = load_config(filename=filename, key=subnet)
    security_group_id = load_config(filename=filename, key=security_group)
    if keypair:
        instances = client.create_instances(
            ImageId=image,
            MinCount=min_count,
            MaxCount=max_count,
            InstanceType=instance_type,
            KeyName=keypair,
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
    else:
        instances = client.create_instances(
            ImageId=image,
            MinCount=min_count,
            MaxCount=max_count,
            InstanceType=instance_type,
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
