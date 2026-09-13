import json
import os
import time
import boto3
import jwt

secrets_client = boto3.client("secretsmanager")
cached_secret = None
cached_secret_time = 0


def get_jwt_secret():
    global cached_secret, cached_secret_time
    now = time.time()
    if cached_secret is None or now - cached_secret_time > 300:
        secret_arn = os.environ["JWT_SECRET_ARN"]
        response = secrets_client.get_secret_value(SecretId=secret_arn)
        cached_secret = json.loads(response["SecretString"])["secret"]
        cached_secret_time = now
    return cached_secret


def handler(event, context):
    token = event.get("authorizationToken", "").replace("Bearer ", "")
    if not token:
        return generate_policy("user", "Deny", event["methodArn"])

    try:
        secret = get_jwt_secret()
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return generate_policy(payload.get("sub", "user"), "Allow", event["methodArn"])
    except jwt.ExpiredSignatureError:
        return generate_policy("user", "Deny", event["methodArn"])
    except jwt.InvalidTokenError:
        return generate_policy("user", "Deny", event["methodArn"])


def generate_policy(principal_id, effect, resource):
    return {
        "principalId": principal_id,
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": effect,
                    "Resource": resource,
                }
            ],
        },
    }
