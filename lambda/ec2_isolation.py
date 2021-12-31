import boto3
import botocore.exceptions
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ec2 = boto3.resource('ec2')

def validate_ec2(ins):
    """Check if given EC2 resource exists."""
    try:
        return ins.state
    except botocore.exceptions.ClientError:
        return False

def lambda_handler(evt, ctx):
    if 'instanceId' in evt:
        tgt = ec2.Instance(evt['instanceId'])
    else:
        logger.error('Did not receive an instance ID.')
        return 

    if not validate_ec2(tgt):
        logger.error(f'EC2 instance with ID \'{tgt.id}\' does not exist.')
        return
    
    logging.info(f'Security groups attached to \'{tgt.id}\':')
    for sg in tgt.security_groups:
        logging.info(f'\t{sg["GroupName"]} ({sg["GroupId"]})')
