"""One-time helper for Task 3: create a Cognito User Pool + App Client so the
AgentCore agent can be deployed with CUSTOM_JWT inbound auth instead of AWS_IAM.

Run once:
    python scripts/setup_cognito.py

Copy the printed discovery_url and app_client_id into your `agentcore add agent`
--discovery-url / --allowed-clients flags.
"""
import json
import os

import boto3

REGION = os.getenv("AWS_REGION", "us-east-1")
POOL_NAME = "agentic-lab-pool"
CLIENT_NAME = "agentic-lab-client"


def main() -> None:
    idp = boto3.client("cognito-idp", region_name=REGION)

    pool = idp.create_user_pool(PoolName=POOL_NAME)
    pool_id = pool["UserPool"]["Id"]

    client = idp.create_user_pool_client(
        UserPoolId=pool_id,
        ClientName=CLIENT_NAME,
        GenerateSecret=False,
        ExplicitAuthFlows=["ALLOW_USER_PASSWORD_AUTH", "ALLOW_REFRESH_TOKEN_AUTH"],
    )
    client_id = client["UserPoolClient"]["ClientId"]

    discovery_url = (
        f"https://cognito-idp.{REGION}.amazonaws.com/{pool_id}/.well-known/openid-configuration"
    )

    print(json.dumps({
        "user_pool_id": pool_id,
        "app_client_id": client_id,
        "discovery_url": discovery_url,
    }, indent=2))


if __name__ == "__main__":
    main()
