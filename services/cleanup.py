from services.ec2 import delete_security_group
from services.transit_gateways import delete_transit_gateway_attachments, delete_transit_gateway
from services.vpc import delete_subnet, delete_vpc
from utils.utils import load_config, update_config


def _cleanup_vpc(vpc_id):
    delete_vpc(vpc_id)


def _cleanup_subnets(subnet_id):
    delete_subnet(subnet_id)


def _cleanup_transit_gateway_attachments(tgw_id):
    delete_transit_gateway_attachments(tgw_id)


def _cleanup_transit_gateway(tgw_id):
    delete_transit_gateway(tgw_id)


def _cleanup_security_groups(sg_id):
    delete_security_group(sg_id)


def cleanup_scenario1():
    filename = 'scenario1'
    data: dict = load_config(filename=filename)
    final_data = data.copy()

    # Delete Transit Gateway Attachments
    for x, y in data.items():
        if 'attach' in x:
            _cleanup_transit_gateway_attachments(y)
            del final_data[x]

    # Delete Transit Gateway
    for x, y in data.items():
        if 'tgw' in x:
            _cleanup_transit_gateway(y)
            del final_data[x]

    # Delete Security Groups
    for x, y in data.items():
        if 'sg_' in x:
            _cleanup_security_groups(y)
            del final_data[x]

    # Delete Subnets
    for x, y in data.items():
        if 'subnet' in x:
            _cleanup_subnets(y)
            del final_data[x]

    # Finally, delete VPC
    for x, y in data.items():
        if 'custom_vpc' in x:
            _cleanup_vpc(y)
            del final_data[x]

    update_config(filename=filename, data=final_data)


if __name__ == '__main__':
    cleanup_scenario1()
