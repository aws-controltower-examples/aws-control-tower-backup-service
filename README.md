<p align="center"> <img src="https://avatars.githubusercontent.com/u/145441379?s=200&v=4" width="130" height="130"></p>


<h1 align="center">
    Control Tower Backup Service
</h1>

<p align="center" style="font-size: 1.2rem;"> 
    CloudFormation Template for Backup Service.
</p>

<p align="center">
<a href="LICENSE">
  <img src="https://img.shields.io/badge/License-APACHE-blue.svg" alt="Licence">
</a>
<a href="https://github.com/aws-controltower-examples/aws-control-tower-securityhub-enabler/actions/workflows/cf-lint.yml">
  <img src="https://github.com/aws-controltower-examples/aws-control-tower-securityhub-enabler/actions/workflows/cf-lint.yml/badge.svg" alt="tfsec">
</a>


</p>
<p align="center">

<a href='https://facebook.com/sharer/sharer.php?u=https://github.com/aws-controltower-examples/aws-control-tower-backup-service-enabler'>
  <img title="Share on Facebook" src="https://user-images.githubusercontent.com/50652676/62817743-4f64cb80-bb59-11e9-90c7-b057252ded50.png" />
</a>
<a href='https://www.linkedin.com/shareArticle?mini=true&title=AWS+Control+Tower+backup-service+Enabler&url=https://github.com/aws-controltower-examples/aws-control-tower-backup-service-enabler'>
  <img title="Share on LinkedIn" src="https://user-images.githubusercontent.com/50652676/62817742-4e339e80-bb59-11e9-87b9-a1f68cae1049.png" />
</a>
<a href='https://twitter.com/intent/tweet/?text=AWS+Control+Tower+backup-service+Enabler&url=https://github.com/aws-controltower-examples/aws-control-tower-backup-service-enabler'>
  <img title="Share on Twitter" src="https://user-images.githubusercontent.com/50652676/62817740-4c69db00-bb59-11e9-8a79-3580fbbf6d5c.png" />
</a>

</p>
<hr>


We eat, drink, sleep and most importantly love **DevOps**. We are working towards strategies for standardizing architecture while ensuring security for the infrastructure. We are strong believer of the philosophy <b>Bigger problems are always solved by breaking them into smaller manageable problems</b>. Resonating with microservices architecture, it is considered best-practice to run database, cluster, storage in smaller <b>connected yet manageable pieces</b> within the infrastructure.

The AWS Control Tower backup-service Enabler is an AWS CloudFormation template designed to simplify the process of enabling and configuring AWS backup-service in the security account of an AWS Control Tower environment. This template creates essential AWS resources, such as IAM roles, Lambda functions, and SNS topics, to automate the backup-service setup based on your specified parameters.

## Prerequisites

Before you proceed, ensure that you have the following prerequisites in place:

### Prerequisites for Deploying the Solution

Before deploying the solution, make sure you have the following prerequisites in place:

1. **AWS Control Tower Environment**: 
   - You must have an AWS Control Tower environment set up.

2. **AWS Organizations Accounts:**
   - You must have four AWS accounts that belong to the same AWS Organizations. Please refer to the documentation on AWS Organizations for more details.
   - Ensure you have placed these accounts within an organization hierarchy.

3. **AWS Organizations Information:**
   - Obtain the following IDs from the AWS Organizations console:
     - AWS Organizations root ID
     - Account ID
     - Organization ID
     - Refer to the AWS Organizations documentation for further information on how to find these IDs.

4. **Setup Supported Resource:**
   - Set up a supported resource in the member accounts to demonstrate the backup functionality. For example, you can use an Amazon EBS volume.
   - Tag each of your EBS volumes with the following tags:
     - Key: "project"
     - Value: "aws-backup-demo"
     - Alternatively, you can use the following tags:
       - Key: "environment"
       - Value: "aws-dev"
   - For more information on creating an Amazon EBS volume, refer to the relevant AWS documentation.

5. **Basic Knowledge:**
   - Ensure you have a basic understanding of the following AWS services and concepts:
     - CloudFormation StackSets
     - Lambda functions
     - Python

6. **AWS CLI Setup:**
   - Install the latest version of the AWS Command Line Interface (CLI) or use the AWS CloudShell.
   - If using the AWS CLI, make sure that you have configured profiles with credentials for the management account in the following files:
     - `~/.aws/credentials`
   - For more information on creating CLI configuration files, consult the AWS CLI user guide.

With these prerequisites in place, you can proceed to deploy the solution.


## Parameters

| Name | Description | Type | Default |
|------|-------------|------| ------- |
| pOrganizationId | The AWS account ID of the Security(Audit) Account. | String | `n/a` |
| pOrgbackupAccounts|        |             |        |
| ExcludedAccounts| A comma-separated list of AWS account IDs to be excluded from backup-service configuration. | String | `""` |
| OrganizationId | AWS Organizations ID for the Control Tower. | String | n/a |
| S3SourceBucket | The S3 bucket containing the backup-service Lambda deployment package. | String | `""` |
| RoleToAssume | The IAM role to be assumed in child accounts to enable backup-service. | String | `AWSControlTowerExecution` |

## Deployment

Follow these steps to deploy the AWS Control Tower backup-service Enabler template:

### **Step 1: Opt in to use AWS Backup**

If this is your first time using the AWS Backup service, you must opt in to use AWS Backup and cross-account management features using the AWS Management Console or CLI.

**To opt in using AWS Management Console (recommended):**

1. Open the AWS Backup console in your management account.

2. From the left navigation pane, choose "Settings."

3. Then, choose "Enable" for the following options:
   - Backup policies
   - Cross-account monitoring
   - Cross-account backup

4. The status of the cross-account management settings would change to "Enabled."

5. Ensure that you have enabled your supported workloads in the Service opt-in.

### **Step 2: Deploy IAM Roles Across Member Accounts**

In this step, you will deploy IAM roles to a single Region across each member account using AWS CloudFormation StackSets. Follow the steps below to create the backup IAM role in each of your member accounts. If you want to learn more about CloudFormation StackSets, you can refer to the blog post on using AWS CloudFormation StackSets for multiple accounts in an AWS Organization.

1. **Log in to your management account** and select the appropriate AWS Region, preferably your AWS Organizations home Region.

2. **Navigate to the AWS CloudFormation StackSets console** in the AWS Region being used and create a new stackset using the `aws-backup-member-account-iam-role.yaml` template.

3. Enter the **StackSet name**. In our example, we use "Backup-Member-Accounts-Role."

4. Under the **Parameters section**, enter values for the following parameters:
   - `pCrossAccountBackupRole`: This is the IAM role name for the cross-account backup role that carries out the backup activities.
   - `pTagKey1`: This is the tag key to assign to resources.
   - `pTagValue1`: This is the tag value to assign to resources.

5. On the **Permissions section**, select the Self-service permissions. We choose the following settings:
   - IAM role name: AWSControlTowerStackSetRole
   - IAM execution role name: AWSControlTowerExecution

6. On the **Set deployment options**, choose "Deploy stacks in organizational units" and provide the OU id consisting of your member accounts. You can also deploy the stackset to specific account id of your member accounts.

7. On the **Specify Regions section**, select a single AWS Region where you want to deploy the member account's IAM roles from the drop-down list. Note: You only need to deploy the backup IAM role to a single Region since IAM roles are global entities. Refer to the [AWS IAM FAQ](https://docs.aws.amazon.com/IAM/latest/UserGuide/using-identity-based-policies-structures.html) for further information.

8. On the **Review page**, validate the parameters and check the box "I acknowledge that AWS CloudFormation might create IAM resource with custom names." Then select "Submit."

9. On the **Stack Instances**, validate the stackset deployment and wait for the status to change from an "OUTDATED" to a "CURRENT" stack instance.



## Functionality

The CloudFormation template creates the following AWS resources:

- **IAM Role:** An IAM role for the backup-service Lambda function with necessary permissions.

- **Lambda Function:** The backup-service Lambda function, responsible for configuring backup-service.

- **SNS Topic:** An SNS topic used for communication between AWS Control Tower and the Lambda function.

- **CloudWatch Event Rules:** Scheduled rules to trigger the Lambda function periodically and when AWS accounts are created or managed via AWS

## Reference links:
![Deployment Steps](https://aws.amazon.com/blogs/storage/automate-centralized-backup-at-scale-across-aws-services-using-aws-backup/)
![Central-Backup setup](https://aws.amazon.com/blogs/storage/centralized-cross-account-management-with-cross-region-copy-using-aws-backup/)

## Feedback 
If you come accross a bug or have any feedback, please log it in our [issue tracker](https://github.com/aws-controltower-examples/aws-control-tower-backup-service-enabler/issues), or feel free to drop us an email at [hello@clouddrove.com](mailto:hello@clouddrove.com).

If you have found it worth your time, go ahead and give us a ★ on [our GitHub](https://github.com/clouddrove/terraform-aws-vpc-peering)!

## About us

At [CloudDrove][website], we offer expert guidance, implementation support and services to help organisations accelerate their journey to the cloud. Our services include docker and container orchestration, cloud migration and adoption, infrastructure automation, application modernisation and remediation, and performance engineering.

<p align="center">We are <b> The Cloud Experts!</b></p>
<hr />
<p align="center">We ❤️  <a href="https://github.com/clouddrove">Open Source</a> and you can check out <a href="https://github.com/clouddrove">our other modules</a> to get help with your new Cloud ideas.</p>

  [website]: https://clouddrove.com
  [github]: https://github.com/clouddrove
  [linkedin]: https://cpco.io/linkedin
  [twitter]: https://twitter.com/clouddrove/
  [email]: https://clouddrove.com/contact-us.html
  [terraform_modules]: https://github.com/clouddrove?utf8=%E2%9C%93&q=terraform-&type=&language=