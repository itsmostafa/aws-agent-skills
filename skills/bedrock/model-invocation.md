# Bedrock Model Invocation Patterns

Advanced patterns for invoking foundation models.

## Model-Specific Invocation

### Claude (Anthropic)

```python
import boto3
import json

bedrock = boto3.client('bedrock-runtime')

def invoke_claude(messages, system=None, max_tokens=1024, temperature=1.0):
    body = {
        'anthropic_version': 'bedrock-2023-05-31',
        'max_tokens': max_tokens,
        'temperature': temperature,
        'messages': messages
    }

    if system:
        body['system'] = system

    response = bedrock.invoke_model(
        modelId='anthropic.claude-3-sonnet-20240229-v1:0',
        contentType='application/json',
        accept='application/json',
        body=json.dumps(body)
    )

    return json.loads(response['body'].read())

# Text generation
result = invoke_claude(
    messages=[{'role': 'user', 'content': 'Explain microservices.'}],
    system='You are a software architect. Be concise.',
    temperature=0.7
)

# With image (Claude 3 vision)
import base64

with open('diagram.png', 'rb') as f:
    image_data = base64.standard_b64encode(f.read()).decode()

result = invoke_claude(
    messages=[{
        'role': 'user',
        'content': [
            {
                'type': 'image',
                'source': {
                    'type': 'base64',
                    'media_type': 'image/png',
                    'data': image_data
                }
            },
            {
                'type': 'text',
                'text': 'Describe this architecture diagram.'
            }
        ]
    }]
)
```

### Titan Text (Amazon)

```python
def invoke_titan_text(prompt, max_tokens=512, temperature=0.7):
    response = bedrock.invoke_model(
        modelId='amazon.titan-text-express-v1',
        contentType='application/json',
        accept='application/json',
        body=json.dumps({
            'inputText': prompt,
            'textGenerationConfig': {
                'maxTokenCount': max_tokens,
                'temperature': temperature,
                'topP': 0.9,
                'stopSequences': []
            }
        })
    )

    result = json.loads(response['body'].read())
    return result['results'][0]['outputText']
```

### Titan Embeddings (Amazon)

```python
def invoke_titan_embeddings(text, dimensions=1024):
    response = bedrock.invoke_model(
        modelId='amazon.titan-embed-text-v2:0',
        contentType='application/json',
        accept='application/json',
        body=json.dumps({
            'inputText': text,
            'dimensions': dimensions,
            'normalize': True
        })
    )

    result = json.loads(response['body'].read())
    return result['embedding']

# Batch embeddings
def batch_embeddings(texts, dimensions=1024):
    embeddings = []
    for text in texts:
        embedding = invoke_titan_embeddings(text, dimensions)
        embeddings.append(embedding)
    return embeddings
```

### Llama (Meta)

```python
def invoke_llama(prompt, max_tokens=512, temperature=0.7):
    response = bedrock.invoke_model(
        modelId='meta.llama3-70b-instruct-v1:0',
        contentType='application/json',
        accept='application/json',
        body=json.dumps({
            'prompt': prompt,
            'max_gen_len': max_tokens,
            'temperature': temperature,
            'top_p': 0.9
        })
    )

    result = json.loads(response['body'].read())
    return result['generation']

# Format for instruction following
prompt = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are a helpful assistant.<|eot_id|>
<|start_header_id|>user<|end_header_id|>
What is Amazon S3?<|eot_id|>
<|start_header_id|>assistant<|end_header_id|>
"""
```

### Mistral

```python
def invoke_mistral(prompt, max_tokens=512, temperature=0.7):
    response = bedrock.invoke_model(
        modelId='mistral.mistral-large-2402-v1:0',
        contentType='application/json',
        accept='application/json',
        body=json.dumps({
            'prompt': f'<s>[INST] {prompt} [/INST]',
            'max_tokens': max_tokens,
            'temperature': temperature,
            'top_p': 0.9
        })
    )

    result = json.loads(response['body'].read())
    return result['outputs'][0]['text']
```

### Stable Diffusion (Image Generation)

```python
import base64

def generate_image(prompt, negative_prompt='', cfg_scale=7, seed=0):
    response = bedrock.invoke_model(
        modelId='stability.stable-diffusion-xl-v1',
        contentType='application/json',
        accept='application/json',
        body=json.dumps({
            'text_prompts': [
                {'text': prompt, 'weight': 1.0},
                {'text': negative_prompt, 'weight': -1.0}
            ],
            'cfg_scale': cfg_scale,
            'seed': seed,
            'steps': 50,
            'width': 1024,
            'height': 1024
        })
    )

    result = json.loads(response['body'].read())
    image_data = base64.b64decode(result['artifacts'][0]['base64'])

    with open('output.png', 'wb') as f:
        f.write(image_data)

    return 'output.png'
```

## Converse API (Unified)

The Converse API provides a unified interface across models.

```python
def converse(messages, model_id, system=None, max_tokens=1024):
    params = {
        'modelId': model_id,
        'messages': messages,
        'inferenceConfig': {
            'maxTokens': max_tokens,
            'temperature': 0.7
        }
    }

    if system:
        params['system'] = [{'text': system}]

    response = bedrock.converse(**params)
    return response['output']['message']['content'][0]['text']

# Works with any supported model
result = converse(
    messages=[
        {'role': 'user', 'content': [{'text': 'What is Lambda?'}]}
    ],
    model_id='anthropic.claude-3-sonnet-20240229-v1:0',
    system='Be concise.'
)
```

### Converse with Tool Use

```python
def converse_with_tools(messages, tools, model_id):
    response = bedrock.converse(
        modelId=model_id,
        messages=messages,
        toolConfig={
            'tools': tools
        }
    )

    output = response['output']['message']

    # Check if model wants to use a tool
    if response['stopReason'] == 'tool_use':
        tool_use = next(
            block for block in output['content']
            if 'toolUse' in block
        )
        return {
            'tool_name': tool_use['toolUse']['name'],
            'tool_input': tool_use['toolUse']['input'],
            'tool_use_id': tool_use['toolUse']['toolUseId']
        }

    return {'text': output['content'][0]['text']}

# Define tools
tools = [{
    'toolSpec': {
        'name': 'get_weather',
        'description': 'Get current weather for a location',
        'inputSchema': {
            'json': {
                'type': 'object',
                'properties': {
                    'location': {
                        'type': 'string',
                        'description': 'City name'
                    }
                },
                'required': ['location']
            }
        }
    }
}]

# Invoke
result = converse_with_tools(
    messages=[
        {'role': 'user', 'content': [{'text': 'What is the weather in Seattle?'}]}
    ],
    tools=tools,
    model_id='anthropic.claude-3-sonnet-20240229-v1:0'
)
```

## RAG with Knowledge Bases

```python
bedrock_agent = boto3.client('bedrock-agent-runtime')

def rag_query(query, knowledge_base_id, model_arn):
    response = bedrock_agent.retrieve_and_generate(
        input={'text': query},
        retrieveAndGenerateConfiguration={
            'type': 'KNOWLEDGE_BASE',
            'knowledgeBaseConfiguration': {
                'knowledgeBaseId': knowledge_base_id,
                'modelArn': model_arn,
                'retrievalConfiguration': {
                    'vectorSearchConfiguration': {
                        'numberOfResults': 5
                    }
                }
            }
        }
    )

    return {
        'answer': response['output']['text'],
        'citations': response.get('citations', [])
    }

# Usage
result = rag_query(
    query='How do I configure S3 bucket policies?',
    knowledge_base_id='KNOWLEDGE_BASE_ID',
    model_arn='arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0'
)
```

### Retrieve Only (No Generation)

```python
def retrieve_context(query, knowledge_base_id, num_results=5):
    response = bedrock_agent.retrieve(
        knowledgeBaseId=knowledge_base_id,
        retrievalQuery={'text': query},
        retrievalConfiguration={
            'vectorSearchConfiguration': {
                'numberOfResults': num_results
            }
        }
    )

    return [
        {
            'text': result['content']['text'],
            'score': result['score'],
            'source': result['location']
        }
        for result in response['retrievalResults']
    ]
```

## Guardrails

```python
def invoke_with_guardrails(prompt, guardrail_id, guardrail_version):
    response = bedrock.invoke_model(
        modelId='anthropic.claude-3-sonnet-20240229-v1:0',
        contentType='application/json',
        accept='application/json',
        body=json.dumps({
            'anthropic_version': 'bedrock-2023-05-31',
            'max_tokens': 1024,
            'messages': [{'role': 'user', 'content': prompt}]
        }),
        guardrailIdentifier=guardrail_id,
        guardrailVersion=guardrail_version
    )

    result = json.loads(response['body'].read())

    # Check if guardrail intervened
    if 'amazon-bedrock-guardrailAction' in response['ResponseMetadata']['HTTPHeaders']:
        return {
            'blocked': True,
            'reason': 'Content policy violation'
        }

    return {
        'blocked': False,
        'text': result['content'][0]['text']
    }
```

## Batch Inference

```python
import boto3

bedrock = boto3.client('bedrock')

def create_batch_job(input_s3_uri, output_s3_uri, model_id, role_arn):
    response = bedrock.create_model_invocation_job(
        jobName=f'batch-job-{int(time.time())}',
        modelId=model_id,
        roleArn=role_arn,
        inputDataConfig={
            's3InputDataConfig': {
                's3Uri': input_s3_uri
            }
        },
        outputDataConfig={
            's3OutputDataConfig': {
                's3Uri': output_s3_uri
            }
        }
    )

    return response['jobArn']

# Input format (JSONL file in S3)
# {"recordId": "1", "modelInput": {"anthropic_version": "...", "messages": [...]}}
# {"recordId": "2", "modelInput": {"anthropic_version": "...", "messages": [...]}}
```

## Error Handling

```python
from botocore.exceptions import ClientError
import time

class BedrockInvoker:
    def __init__(self, model_id):
        self.bedrock = boto3.client('bedrock-runtime')
        self.model_id = model_id

    def invoke(self, body, max_retries=3):
        last_error = None

        for attempt in range(max_retries):
            try:
                response = self.bedrock.invoke_model(
                    modelId=self.model_id,
                    contentType='application/json',
                    accept='application/json',
                    body=json.dumps(body)
                )
                return json.loads(response['body'].read())

            except ClientError as e:
                error_code = e.response['Error']['Code']
                last_error = e

                if error_code == 'ThrottlingException':
                    wait_time = (2 ** attempt) + random.random()
                    time.sleep(wait_time)
                elif error_code == 'ModelNotReadyException':
                    time.sleep(5)
                elif error_code == 'ValidationException':
                    raise  # Don't retry validation errors
                else:
                    raise

        raise last_error
```

## Provisioned Throughput

```bash
# Create provisioned throughput
aws bedrock create-provisioned-model-throughput \
  --model-id anthropic.claude-3-sonnet-20240229-v1:0 \
  --provisioned-model-name my-claude-capacity \
  --model-units 1

# Use provisioned model
aws bedrock-runtime invoke-model \
  --model-id arn:aws:bedrock:us-east-1:123456789012:provisioned-model/my-claude-capacity \
  --body '...' \
  response.json
```

```python
# Invoke provisioned model
response = bedrock.invoke_model(
    modelId='arn:aws:bedrock:us-east-1:123456789012:provisioned-model/my-claude-capacity',
    contentType='application/json',
    accept='application/json',
    body=json.dumps(body)
)
```

## VPC Endpoint

```yaml
# CloudFormation for private Bedrock access
Resources:
  BedrockEndpoint:
    Type: AWS::EC2::VPCEndpoint
    Properties:
      VpcId: !Ref VPC
      ServiceName: !Sub com.amazonaws.${AWS::Region}.bedrock-runtime
      VpcEndpointType: Interface
      SubnetIds:
        - !Ref PrivateSubnet1
        - !Ref PrivateSubnet2
      SecurityGroupIds:
        - !Ref BedrockSecurityGroup
      PrivateDnsEnabled: true

  BedrockSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      VpcId: !Ref VPC
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 443
          ToPort: 443
          SourceSecurityGroupId: !Ref AppSecurityGroup
```
