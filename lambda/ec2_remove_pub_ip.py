import boto3 
import botocore.exceptions
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ec2 = boto3.resource('ec2')
ec2_c = boto3.client('ec2')

# Receives an instance object, returns True if it exists
def validate_ec2(ins):
    try:
        return ins.state
    except botocore.exceptions.ClientError:
        return False

def lambda_handler(evt, ctx):
    # Validate provided data
    if 'instanceId' in evt:
        tgt = ec2.Instance(evt['instanceId'])
    else:
        logger.error('Did not receive an instance ID.')
        return 

    # Ensure instance exists
    if not validate_ec2(tgt):
        logger.error(f'EC2 instance with ID \'{tgt.id}\' does not exist.')
        return

    pub_ip = tgt.public_ip_address 
    if pub_ip:
        logging.warn(f'Instance has a static public IP: {pub_ip}.')

    # Get instance Elastic IPs
    for vpcaddr in tgt.vpc_addresses.all():
        ec2_c.disassociate_address(vpcaddr.association_id)
        logging.info(f'Disassociated: {vpcaddr.public_ip}')

