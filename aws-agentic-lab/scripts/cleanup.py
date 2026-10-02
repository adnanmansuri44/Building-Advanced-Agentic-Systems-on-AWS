"""Task 4: tear down everything created for the lab to avoid ongoing charges.

Run from inside the AgentCore project folder created in Task 3
(e.g. aws-agentic-lab/AgenticLab):
    ..\\.venv\\Scripts\\python.exe ..\\scripts\\cleanup.py
"""
import os
import subprocess

import boto3

REGION = os.getenv("AWS_REGION", "us-east-1")
COGNITO_POOL_NAME = "agentic-lab-pool"
CDK_BOOTSTRAP_STACK_NAME = "CDKToolkit"


def remove_agentcore_resources() -> None:
    # Deletes every AgentCore resource tracked in this project's agentcore.json
    agentcore_command = "agentcore.cmd" if os.name == "nt" else "agentcore"
    subprocess.run([agentcore_command, "remove", "all", "-y"], check=True)
    subprocess.run([agentcore_command, "deploy", "-y"], check=True)


def delete_cdk_bootstrap_stack() -> None:
    cloudformation = boto3.client("cloudformation", region_name=REGION)
    stack_summaries = [
        stack
        for page in cloudformation.get_paginator("list_stacks").paginate()
        for stack in page.get("StackSummaries", [])
        if stack["StackName"] == CDK_BOOTSTRAP_STACK_NAME
        and stack["StackStatus"] != "DELETE_COMPLETE"
    ]
    if not stack_summaries:
        print(f"No {CDK_BOOTSTRAP_STACK_NAME} stack found in {REGION}.")
        return

    stack = max(stack_summaries, key=lambda summary: summary["CreationTime"])
    stack_id = stack["StackId"]
    bucket_names = [
        resource["PhysicalResourceId"]
        for page in cloudformation.get_paginator("list_stack_resources").paginate(StackName=stack_id)
        for resource in page.get("StackResourceSummaries", [])
        if resource["LogicalResourceId"] == "StagingBucket"
        and resource.get("PhysicalResourceId")
    ]
    if stack["StackStatus"] != "DELETE_IN_PROGRESS":
        cloudformation.delete_stack(StackName=stack_id)

    cloudformation.get_waiter("stack_delete_complete").wait(StackName=stack_id)
    print(f"Deleted {CDK_BOOTSTRAP_STACK_NAME} CloudFormation stack in {REGION}.")
    for bucket_name in bucket_names:
        delete_versioned_bucket(bucket_name)


def delete_versioned_bucket(bucket_name: str) -> None:
    s3 = boto3.client("s3", region_name=REGION)
    try:
        paginator = s3.get_paginator("list_object_versions")
        for page in paginator.paginate(Bucket=bucket_name):
            objects = [
                {"Key": version["Key"], "VersionId": version["VersionId"]}
                for collection in ("Versions", "DeleteMarkers")
                for version in page.get(collection, [])
            ]
            for start in range(0, len(objects), 1000):
                response = s3.delete_objects(
                    Bucket=bucket_name,
                    Delete={"Objects": objects[start : start + 1000], "Quiet": True},
                )
                if response.get("Errors"):
                    raise RuntimeError(f"Could not empty CDK asset bucket {bucket_name}: {response['Errors']}")
        s3.delete_bucket(Bucket=bucket_name)
    except s3.exceptions.NoSuchBucket:
        return
    print(f"Deleted retained CDK asset bucket: {bucket_name}")


def delete_cognito_pool() -> None:
    idp = boto3.client("cognito-idp", region_name=REGION)
    for pool in idp.list_user_pools(MaxResults=60)["UserPools"]:
        if pool["Name"] == COGNITO_POOL_NAME:
            idp.delete_user_pool(UserPoolId=pool["Id"])
            print(f"Deleted Cognito user pool: {pool['Name']} ({pool['Id']})")


if __name__ == "__main__":
    remove_agentcore_resources()
    delete_cdk_bootstrap_stack()
    delete_cognito_pool()
    print(
        "Cleanup complete. Verify in the AWS console: Bedrock AgentCore, ECR, "
        "Cognito, CloudWatch Logs, and IAM roles."
    )
