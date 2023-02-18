import logging
import boto3
import yaml
from botocore.exceptions import ClientError

from utils.utils import store_config, load_config, CONFIG_PATH, fetch_constants

logger = logging.getLogger()
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s: %(levelname)s: %(message)s')

client = boto3.resource('ec2')
ec2client = client.meta.client


def create_vpc(name: str, ip_cidr: str, filename: str, persist: bool):
    vpc = __create_vpc_util(name=name, ip_cidr=ip_cidr)
    logger.info(f'Custom VPC created: {vpc}')
    if persist:
        store_config(value=vpc.id, key=name, filename=filename)
    return vpc


def __create_vpc_util(name: str, ip_cidr: str):
    try:
        vpc = client.create_vpc(CidrBlock=ip_cidr,
                                InstanceTenancy='default',
                                TagSpecifications=[{
                                    'ResourceType': 'vpc',
                                    'Tags': [{'Key': 'Name', 'Value': name}]}])
        vpc.wait_until_available()
    except ClientError as e:
        logger.exception('Could not delete the VPC', e)
    else:
        return vpc


def create_subnet(subnet_name: str, subnet_ip_cidr: str, vpc_name: str, filename: str, persist: bool):
    vpc_id = load_config(filename=filename, key=vpc_name)
    subnet = __create_subnet_util(subnet_name=subnet_name, subnet_cidr=subnet_ip_cidr, vpc_id=vpc_id)
    logger.info(f'Subnet created: {subnet}')
    if persist:
        store_config(subnet['Subnet']['SubnetId'], subnet_name, filename=filename)
    return subnet


def __create_subnet_util(subnet_name: str, subnet_cidr: str, vpc_id: str):
    try:
        subnet = ec2client.create_subnet(CidrBlock=subnet_cidr,
                                         VpcId=vpc_id,
                                         AvailabilityZone='us-east-1d',
                                         TagSpecifications=[{
                                             'ResourceType': 'subnet',
                                             'Tags': [{'Key': 'Name', 'Value': subnet_name}]}
                                         ])  # Availability zone is hardcoded for testing purposes
    except ClientError as e:
        logger.exception('Could not create a subnet', e)
    else:
        return subnet


def delete_subnet(subnet_id):
    try:
        response = ec2client.delete_subnet(subnet_id)
    except ClientError as e:
        logger.exception('Could not delete subnet', e)
    else:
        return response


def delete_vpc(vpc_id: str):
    try:
        response = ec2client.delete_vpc(VpcId=vpc_id)
    except ClientError as e:
        logger.exception('Could not delete the VPC', e)
    else:
        return response


def create_internet_gateways(ig_name: str, filename: str, persist=True):
    try:
        igw = ec2client.create_internet_gateway()
        logger.info(f'Internet Gateway created: {igw}')
        if persist:
            store_config(value=igw['InternetGateway']['InternetGatewayId'], key=ig_name, filename=filename)
    except ClientError as e:
        logger.exception('Could not create an internet gateway', e)
    else:
        return igw


def attach_vpc_with_ig(vpc: str, igw: str, filename: str):
    try:
        vpc_id = load_config(filename=filename, key=vpc)
        vpc_client = client.Vpc(vpc_id)
        ig_id = load_config(filename=filename, key=igw)

        res = vpc_client.attach_internet_gateway(InternetGatewayId=ig_id)
        logger.info(f'Attaching {ig_id} with {vpc_id}')
    except ClientError as e:
        logger.exception('Could not attach vpc to ig', e)
    else:
        return res


def create_routing_table_associate(route_table_name: str, vpc: str, subnet: str, filename: str, persist: bool):
    try:
        vpc_id = load_config(filename=filename, key=vpc)
        subnet_id = load_config(filename=filename, key=subnet)
        vpc_client = client.Vpc(vpc_id)
        route_table = vpc_client.create_route_table(TagSpecifications=[
            {
                'ResourceType': 'route-table',
                'Tags': [
                    {
                        'Key': "Name",
                        'Value': route_table_name
                    },
                ]
            },
        ])
        logger.info(f"Route table created: {route_table}")
        if persist:
            store_config(value=route_table.route_table_id, key=route_table_name, filename=filename)
        response = route_table.associate_with_subnet(SubnetId=subnet_id)
        logger.info(f"Route Table {route_table} associated with subnet {subnet_id}: {response}")
    except ClientError as e:
        logger.exception('Could not create routing table', e)
    else:
        return route_table


def create_route_with_igw(igw: str, route_table: str, destination_ip_cidr: str, filename: str):
    route_table_id = load_config(filename=filename, key=route_table)
    igw_id = load_config(filename=filename, key=igw)
    route = ec2client.create_route(DestinationCidrBlock=destination_ip_cidr,
                                   RouteTableId=route_table_id,
                                   GatewayId=igw_id)
    if route:
        logger.info(f"Route created for {igw_id} with {destination_ip_cidr}")


def find_existing_route_tables(route_table_name: str, vpc: str, filename: str, persist=True):
    vpc1_id = load_config(filename=filename, key=vpc)
    vpc1_client = client.Vpc(vpc1_id)
    route_tables = vpc1_client.route_tables.all()
    rt = [x for x in route_tables]
    if rt is not None:
        logger.info('Route Tables found: ', rt[0].id)
        if persist:
            store_config(value=rt[0].id, key=route_table_name, filename='scenario1')
    else:
        logger.exception('No Route tables found')
    return


if __name__ == '__main__':
    pass
