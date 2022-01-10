import boto3
import botocore.exceptions
import logging

ISOLATION_SG = "csec-ec2-isolation"

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ec2 = boto3.resource('ec2')

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
    
    # Write out the list of security groups attached to the instance
    for sg in tgt.security_groups:
        logging.info(f'Revoking: {sg["GroupName"]} ({sg["GroupId"]})')

    # Generate a list of all security groups in the instance's VPC
    vpc = ec2.Vpv(tgt.vpc_id)
    vpc_sg_query = ec2.security_groups.filter(
        Filters = [
            {'Name': 'vpc-id', 'Values': [tgt.vpc_id]},
            {'Name': 'group-name', 'Values': [ISOLATION_SG]}
        ]
    )

    try:
        vpc_sg_list = list(vpc_sg_query)
    except:
        vpc_sg_list = []

    # Create the isolation group if it doesnt exist
    if vpc_sg_list:
        iso_sg = ec2.SecurityGroup(vpc_sg_list[0].id)
        logging.info(f'Discovered isolation group already created with ID: {iso_sg.id}')
    else:
        iso_sg = vpc.create_security_group(
            Description='Used by CSIRT team to isolate EC2 instances from the network',
            GroupName=ISOLATION_SG
        )

        logging.info(f'Created isolation group with ID: {iso_sg.id}')

        iso_sg.revoke_egress(
            IpPermissions = [{
                'IpProtocol': '-1',
                'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
            }]
        )

    # Add the isolation group to the instance
    tgt.modify_attribute(Groups=[iso_sg.id])

    
