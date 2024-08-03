import json
import os
import boto3
from botocore.exceptions import ClientError

_env_keys = None

def load_keys():
    global _env_keys
    if _env_keys is not None:
        return _env_keys

    fizit_env = os.environ.get('FIZIT_ENV')
    if not fizit_env:
        raise EnvironmentError("The FIZIT_ENV environment variable must be set to 'dev', 'test', or 'main'.")

    _env_keys = {}
    secret_prefix = {'dev': 'devnet', 'test': 'testnet', 'main': 'mainnet'}.get(fizit_env)

    if not secret_prefix:
        raise ValueError("FIZIT_ENV must be 'dev', 'test', or 'main'.")

    secrets_to_load = [f"{secret_prefix}/rotating-keys", f"{secret_prefix}/static-keys"]
    region_name = "us-east-1"

    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    for secret_name in secrets_to_load:
        try:
            print(f"Fetching secret value for {secret_name} from AWS Secrets Manager")
            get_secret_value_response = client.get_secret_value(SecretId=secret_name)

            if 'SecretString' in get_secret_value_response:
                secrets = json.loads(get_secret_value_response['SecretString'])
                _env_keys.update(secrets)
            else:
                print(f"No SecretString found in the response for {secret_name}")

        except ClientError as e:
            print(f"Error fetching secrets: {e}")

    return _env_keys