# Cognito Authentication Flows

Detailed authentication flows and OAuth configurations.

## Authentication Flows

### USER_SRP_AUTH (Recommended)

Secure Remote Password protocol - password never sent over network.

```python
import boto3
from warrant.aws_srp import AWSSRP

cognito = boto3.client('cognito-idp')

# Use warrant library for SRP
aws_srp = AWSSRP(
    username='user@example.com',
    password='password',
    pool_id='us-east-1_abc123',
    client_id='client-id',
    client_secret='client-secret'
)

tokens = aws_srp.authenticate_user()
```

### USER_PASSWORD_AUTH

Direct username/password (requires enabling in client settings).

```python
response = cognito.initiate_auth(
    ClientId='client-id',
    AuthFlow='USER_PASSWORD_AUTH',
    AuthParameters={
        'USERNAME': 'user@example.com',
        'PASSWORD': 'password',
        'SECRET_HASH': get_secret_hash(...)
    }
)
```

### CUSTOM_AUTH

Custom authentication flow with Lambda triggers.

```python
# Step 1: Initiate
response = cognito.initiate_auth(
    ClientId='client-id',
    AuthFlow='CUSTOM_AUTH',
    AuthParameters={
        'USERNAME': 'user@example.com'
    }
)

# Step 2: Respond to challenge
response = cognito.respond_to_auth_challenge(
    ClientId='client-id',
    ChallengeName='CUSTOM_CHALLENGE',
    Session=response['Session'],
    ChallengeResponses={
        'USERNAME': 'user@example.com',
        'ANSWER': 'custom-answer'
    }
)
```

## OAuth 2.0 Flows

### Authorization Code Flow (Recommended for web)

```
1. Redirect to authorize endpoint:
   https://my-domain.auth.us-east-1.amazoncognito.com/oauth2/authorize?
   response_type=code&
   client_id=CLIENT_ID&
   redirect_uri=https://myapp.com/callback&
   scope=openid+email+profile

2. User authenticates, redirected back with code:
   https://myapp.com/callback?code=AUTHORIZATION_CODE

3. Exchange code for tokens:
```

```python
import requests

response = requests.post(
    'https://my-domain.auth.us-east-1.amazoncognito.com/oauth2/token',
    data={
        'grant_type': 'authorization_code',
        'client_id': 'CLIENT_ID',
        'client_secret': 'CLIENT_SECRET',
        'code': 'AUTHORIZATION_CODE',
        'redirect_uri': 'https://myapp.com/callback'
    },
    headers={'Content-Type': 'application/x-www-form-urlencoded'}
)

tokens = response.json()
```

### Authorization Code Flow with PKCE (Mobile/SPA)

```python
import secrets
import hashlib
import base64

# Generate PKCE values
code_verifier = secrets.token_urlsafe(64)
code_challenge = base64.urlsafe_b64encode(
    hashlib.sha256(code_verifier.encode()).digest()
).decode().rstrip('=')

# Step 1: Authorization URL with PKCE
auth_url = (
    f'https://my-domain.auth.us-east-1.amazoncognito.com/oauth2/authorize?'
    f'response_type=code&'
    f'client_id={client_id}&'
    f'redirect_uri={redirect_uri}&'
    f'scope=openid+email&'
    f'code_challenge={code_challenge}&'
    f'code_challenge_method=S256'
)

# Step 2: Exchange code with verifier
response = requests.post(
    'https://my-domain.auth.us-east-1.amazoncognito.com/oauth2/token',
    data={
        'grant_type': 'authorization_code',
        'client_id': client_id,
        'code': authorization_code,
        'redirect_uri': redirect_uri,
        'code_verifier': code_verifier
    }
)
```

### Implicit Flow (Legacy, not recommended)

```
https://my-domain.auth.us-east-1.amazoncognito.com/oauth2/authorize?
response_type=token&
client_id=CLIENT_ID&
redirect_uri=https://myapp.com/callback&
scope=openid+email

Callback: https://myapp.com/callback#id_token=TOKEN&access_token=TOKEN
```

### Client Credentials Flow (Machine-to-Machine)

```bash
# Create resource server
aws cognito-idp create-resource-server \
  --user-pool-id us-east-1_abc123 \
  --identifier api.myapp.com \
  --name "My API" \
  --scopes ScopeName=read,ScopeDescription="Read access" \
          ScopeName=write,ScopeDescription="Write access"

# Create client for M2M
aws cognito-idp create-user-pool-client \
  --user-pool-id us-east-1_abc123 \
  --client-name service-client \
  --generate-secret \
  --allowed-o-auth-flows client_credentials \
  --allowed-o-auth-scopes api.myapp.com/read api.myapp.com/write \
  --allowed-o-auth-flows-user-pool-client
```

```python
import requests
import base64

credentials = base64.b64encode(f'{client_id}:{client_secret}'.encode()).decode()

response = requests.post(
    'https://my-domain.auth.us-east-1.amazoncognito.com/oauth2/token',
    data={
        'grant_type': 'client_credentials',
        'scope': 'api.myapp.com/read api.myapp.com/write'
    },
    headers={
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Basic {credentials}'
    }
)
```

## MFA Flows

### SMS MFA

```python
# After initial auth, if MFA required:
if response.get('ChallengeName') == 'SMS_MFA':
    response = cognito.respond_to_auth_challenge(
        ClientId='client-id',
        ChallengeName='SMS_MFA',
        Session=response['Session'],
        ChallengeResponses={
            'USERNAME': 'user@example.com',
            'SMS_MFA_CODE': '123456',
            'SECRET_HASH': get_secret_hash(...)
        }
    )
```

### TOTP MFA

```python
# Associate TOTP
response = cognito.associate_software_token(
    AccessToken=access_token
)
secret_code = response['SecretCode']

# Verify TOTP
cognito.verify_software_token(
    AccessToken=access_token,
    UserCode='123456',
    FriendlyDeviceName='My Phone'
)

# Set as preferred
cognito.set_user_mfa_preference(
    AccessToken=access_token,
    SoftwareTokenMfaSettings={
        'Enabled': True,
        'PreferredMfa': True
    }
)
```

## Lambda Triggers

### Pre Sign-up

```python
def handler(event, context):
    # Auto-confirm users from specific domains
    email = event['request']['userAttributes'].get('email', '')
    if email.endswith('@mycompany.com'):
        event['response']['autoConfirmUser'] = True
        event['response']['autoVerifyEmail'] = True

    return event
```

### Pre Authentication

```python
def handler(event, context):
    # Block specific users
    username = event['userName']
    if is_blocked(username):
        raise Exception('User is blocked')

    return event
```

### Post Confirmation

```python
def handler(event, context):
    # Add user to group after confirmation
    cognito = boto3.client('cognito-idp')

    cognito.admin_add_user_to_group(
        UserPoolId=event['userPoolId'],
        Username=event['userName'],
        GroupName='Users'
    )

    return event
```

### Custom Message

```python
def handler(event, context):
    if event['triggerSource'] == 'CustomMessage_SignUp':
        event['response']['emailSubject'] = 'Welcome to MyApp!'
        event['response']['emailMessage'] = f'''
            Hi {event['request']['userAttributes']['name']},
            Your verification code is {event['request']['codeParameter']}
        '''

    return event
```

### Define Auth Challenge

```python
def handler(event, context):
    if len(event['request']['session']) == 0:
        # First challenge
        event['response']['challengeName'] = 'CUSTOM_CHALLENGE'
        event['response']['issueTokens'] = False
        event['response']['failAuthentication'] = False
    elif event['request']['session'][-1]['challengeResult']:
        # Challenge passed
        event['response']['issueTokens'] = True
        event['response']['failAuthentication'] = False

    return event
```

## Social Identity Providers

### Configure Google

```bash
aws cognito-idp create-identity-provider \
  --user-pool-id us-east-1_abc123 \
  --provider-name Google \
  --provider-type Google \
  --provider-details '{
    "client_id": "google-client-id",
    "client_secret": "google-client-secret",
    "authorize_scopes": "profile email openid"
  }' \
  --attribute-mapping '{
    "email": "email",
    "name": "name",
    "picture": "picture"
  }'
```

### Configure SAML

```bash
aws cognito-idp create-identity-provider \
  --user-pool-id us-east-1_abc123 \
  --provider-name MySAML \
  --provider-type SAML \
  --provider-details '{
    "MetadataFile": "<SAML metadata XML>",
    "IDPSignout": "true"
  }' \
  --attribute-mapping '{
    "email": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress"
  }'
```

## Token Management

### Verify Token

```python
import jwt
from jwt import PyJWKClient

def verify_cognito_token(token, user_pool_id, client_id, region='us-east-1'):
    jwks_url = f'https://cognito-idp.{region}.amazonaws.com/{user_pool_id}/.well-known/jwks.json'
    issuer = f'https://cognito-idp.{region}.amazonaws.com/{user_pool_id}'

    jwk_client = PyJWKClient(jwks_url)
    signing_key = jwk_client.get_signing_key_from_jwt(token)

    claims = jwt.decode(
        token,
        signing_key.key,
        algorithms=['RS256'],
        audience=client_id,
        issuer=issuer
    )

    return claims
```

### Revoke Tokens

```python
cognito.revoke_token(
    Token=refresh_token,
    ClientId='client-id',
    ClientSecret='client-secret'
)
```

### Global Sign Out

```python
cognito.global_sign_out(
    AccessToken=access_token
)
```
