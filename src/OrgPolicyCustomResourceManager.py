# pylint: disable = C0103, R0902, W1203, C0301, W0311
"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

Permission is hereby granted, free of charge, to any person obtaining a copy of this
software and associated documentation files (the "Software"), to deal in the Software
without restriction, including without limitation the rights to use, copy, modify,
merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

This file contains the code for the Lambda function that handles custom
cloudformation resource management for Organization policies
"""
import time
import json
import logging
import urllib3
import boto3


logger = logging.getLogger()
logger.setLevel(logging.INFO)
org_client = boto3.client('organizations')

def get_policy(event):
    """
    Helper function for getting the policy contents from the event object. This function
    will extract the policy from an S3 location if PolicyBucket and PolicyLocation is provided
    """
    policy_contents = ''
    if 'PolicyContents' in event['ResourceProperties']:
        policy_contents = event['ResourceProperties']['PolicyContents']
    else:
        s3_bucket = event['ResourceProperties']['PolicyBucket']
        s3_object = event['ResourceProperties']['PolicyLocation']
        s3 = boto3.resource('s3')
        policy_file = s3.Object(s3_bucket, s3_object)
        policy_contents = policy_file.get()['Body'].read().decode('utf-8')

    #logger.info(f"policy_contents : {policy_contents}")
    #Check for replacement variables
    if 'Variables' in event['ResourceProperties']:
        variables= event['ResourceProperties']['Variables']
        logger.info(f"variables : {variables}")
        for variable in variables:
            for key, value in variable.items():
              logger.info(f"Replacing Key : {key} with value : {value}")
              policy_contents = policy_contents.replace(key,value )
    return json.loads(policy_contents)

def lambda_handler(event, context):
      """
      Main Lambda handler function. This function will handle the Create, Update and Delete operation requests
      from CloudFormation
      """
      try:
        #create physical resource id
        physical_resource_id = 'OrgPolicyCustomResourceManager'
        status = 'SUCCESS'

        if 'PhysicalResourceId' in event:
          physical_resource_id = event['PhysicalResourceId']

        logger.info(f"OrgPolicyCustomResourceManager Request: {event}")
        resource_action = event['RequestType']
        policy_prefix = event['ResourceProperties']['PolicyPrefix']
        policy_contents = get_policy(event)
        policy_type = event['ResourceProperties']['PolicyType']
        policy_description = event['ResourceProperties']['PolicyDescription']

        policy_target_list=[]
        if 'PolicyTargets' in event['ResourceProperties']:
          policy_targets = event['ResourceProperties']['PolicyTargets']
          policy_target_list = policy_targets

        logger.info(f"policy_targets: {policy_targets}")

        if resource_action == 'Create':
          
          policy_id_list = create_and_attach_policies(policy_prefix,policy_description, policy_type,policy_contents,policy_target_list)
          response_data = {
                'PolicyPrefix': policy_prefix,
                'PolicyIdList': policy_id_list,
                'PolicyType': policy_type,
                'PolicyTargets': policy_target_list,
                'Message': 'Policies created and attached successfully'
          }
        elif resource_action in ('Update' , 'Delete'):
          logger.info(f" Action: {resource_action} policy, policy_type: {policy_type}, policy_prefix : {policy_prefix}")
          response = org_client.list_policies(Filter=policy_type)
          policyList = list(filter(lambda item: item['Name'].startswith(policy_prefix), response["Policies"]))
          logger.info(f"Policy Found : {policyList}, Length : {len(policyList)}")

          if not policyList and len(policyList) == 0:
              logger.error(f'Policy not found with prefix : {policy_prefix}')
              response_data = {
                              'Message': 'Policy not found for prefix : ' + policy_prefix
              }
              status = 'FAILED'
          else:

            for policy in policyList:
              policy_id=policy['Id']

              response = org_client.list_targets_for_policy(PolicyId=policy_id)
              if 'Targets' in response:

                  curr_policy_target_list = []
                  for target in response['Targets']:
                      curr_policy_target_list.append(target['TargetId'])

                  #Detach the policy from existing list
                  detach_policy_from_target_list(curr_policy_target_list,policy_id)

              #delete policies neverthless to allow new creation
              try:
                  response = org_client.delete_policy(PolicyId=policy_id)
                  logger.info(f"deletePolicy response: {response}")
              except Exception as e:  # pylint: disable = W0703
                  logger.error(str(e))

            if resource_action == 'Delete':
                  response_data = {'Message': 'Policy(s) deleted successfully'}
            elif resource_action == 'Update':
              #Create and attach policies with new contents
              policy_id_list = create_and_attach_policies(policy_prefix,policy_description, policy_type,policy_contents,policy_target_list)
              response_data = {'PolicyIdList': policy_id_list,'Message': 'Policies modified and attached successfully'}
              
        else:
          logger.error(f"Unexpected Action : {resource_action}")
          response_data = {
                          'Message': 'Unexpected event received from CloudFormation'
          }
          status = 'FAILED'
      except Exception as exc:
        logger.error(f"Exception: {str(exc)}")
        response_data = {
                      'Message': str(exc)
        }
        status = 'FAILED'

      #Send the response for the CFN Stack operation request
      send(event, context, status, response_data, physical_resource_id)

def create_and_attach_policies(policy_prefix,policy_description, policy_type,policy_contents,policy_target_list):
    """
    Helper function to create and attach the policies to the targets
    """  
    policy_count = 0
    policy_name_list = []
    policy_id_list = []
    for policy_content in policy_contents:
          policy_name = policy_prefix + '-{:0>2}'.format(policy_count)
          policy_name_list.append(policy_name)
          logger.info(f"Create and update policy with contents : {json.dumps(policy_content)} for name : {policy_name}")
          response = org_client.create_policy(
                Content=json.dumps(policy_content),
                Description=policy_description,
                Name=policy_name,
                Type=policy_type
          )
          logger.info(f"Response: {response}")
          policy_id = response['Policy']['PolicySummary']['Id']
          policy_id_list.append(policy_id)
          policy_count = policy_count + 1
    
    logger.info(f'Policy creation complete, policy_id_list :{policy_id_list}, policy_name_list :{policy_name_list}')
    
    attach_policy(policy_id_list,policy_target_list)
    
    return policy_id_list
          
def attach_policy(policy_id_list,policy_target_list):
    """
    Helper function to attach the specified policy to a list of targets
    """
    logger.info(f"attach_policy for {policy_id_list} on {policy_target_list}")
    #Attach the policy in target accounts
    for policy_id in policy_id_list:
      for policyTarget in policy_target_list:
          try:
            #To avoid ConcurrentModificationException 
            time.sleep(int(5))
            logger.info(f"Attaching {policy_id} on Account {policyTarget}")
            org_client.attach_policy(PolicyId=policy_id,
                                          TargetId=policyTarget)

            logger.info(f"Attached {policy_id} on Account {policyTarget}")
          except Exception as e:  # pylint: disable = W0703
              logger.error(str(e))

def detach_policy(policy_id,policy_target):
    """
    Helper function to detach the specified policy from policy_target
    """
    try:
        logger.info(f"Detaching {policy_id} from Account {policy_target}")
        response = org_client.detach_policy(PolicyId=policy_id,
                                    TargetId=policy_target)
        logger.info(f"Detached {policy_id} from Account {policy_target}, Response : {response}")
    except org_client.exceptions.PolicyNotAttachedException:
        logger.info('Ignoring error to continue trying for further detachments.')

def detach_policy_from_target_list(policy_target_list,policy_id):
    """
    Helper function to detach the specified policy from policy_target_list
    """
    #Detach the policy in target accounts
    for policy_target in policy_target_list:
        try:
            detach_policy(policy_id,policy_target)
        except org_client.exceptions.PolicyInUseException:
            time.sleep(int(1))
            detach_policy(policy_id,policy_target)

        except org_client.exceptions.PolicyNotAttachedException:
            logger.info('Ignoring error to continue trying for further detachments.')

def update_policy(policy_id, policy_content):
      """
      Helper function update the policy at the organization level.
      """
      logger.info(f"update_policy for policy_id : {policy_id}")
      org_client.update_policy(PolicyId=policy_id,Content=json.dumps(policy_content))

def send(event, context, response_status, response_data, physical_resource_id, no_echo=False):  # pylint: disable = R0913
      """
      Helper function for sending updates on the custom resource to CloudFormation during a
      'Create', 'Update', or 'Delete' event.
      """

      http = urllib3.PoolManager()
      response_url = event['ResponseURL']

      json_response_body = json.dumps({
          'Status': response_status,
          'Reason': response_data['Message'] + f', See the details in CloudWatch Log Stream: {context.log_stream_name}',
          'PhysicalResourceId': physical_resource_id,
          'StackId': event['StackId'],
          'RequestId': event['RequestId'],
          'LogicalResourceId': event['LogicalResourceId'],
          'NoEcho': no_echo,
          'Data': response_data
      }).encode('utf-8')

      headers = {
          'content-type': '',
          'content-length': str(len(json_response_body))
      }

      try:
          http.request('PUT', response_url,
                        body=json_response_body, headers=headers)
      except Exception as e:  # pylint: disable = W0703
          logger.error(e)