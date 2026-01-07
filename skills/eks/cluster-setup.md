# EKS Cluster Setup

Comprehensive cluster configuration and setup patterns.

## Cluster Architecture Options

### Public Cluster

API server accessible from internet, nodes in public subnets.

```bash
eksctl create cluster \
  --name my-cluster \
  --region us-east-1 \
  --nodegroup-name standard-workers \
  --node-type t3.medium \
  --nodes 3
```

### Private Cluster

API server only accessible from VPC.

```bash
eksctl create cluster \
  --name my-cluster \
  --region us-east-1 \
  --nodegroup-name standard-workers \
  --node-type t3.medium \
  --nodes 3 \
  --node-private-networking \
  --vpc-private-subnets subnet-private1,subnet-private2
```

### Fully Private Cluster

No public access at all, requires VPN/Direct Connect.

```bash
aws eks create-cluster \
  --name my-cluster \
  --role-arn arn:aws:iam::123456789012:role/eks-cluster-role \
  --resources-vpc-config \
    subnetIds=subnet-private1,subnet-private2,\
    endpointPublicAccess=false,\
    endpointPrivateAccess=true
```

## VPC Configuration

### Required Subnets

- **Control plane**: Needs subnets in at least 2 AZs
- **Worker nodes**: Can be public or private
- **Load balancers**: Need subnets tagged appropriately

### Subnet Tags

```bash
# Public subnets (for public load balancers)
aws ec2 create-tags \
  --resources subnet-12345678 \
  --tags Key=kubernetes.io/role/elb,Value=1

# Private subnets (for internal load balancers)
aws ec2 create-tags \
  --resources subnet-87654321 \
  --tags Key=kubernetes.io/role/internal-elb,Value=1

# Cluster ownership (required for all subnets)
aws ec2 create-tags \
  --resources subnet-12345678 subnet-87654321 \
  --tags Key=kubernetes.io/cluster/my-cluster,Value=shared
```

### VPC CNI Configuration

```bash
# Enable prefix delegation for more IPs per node
kubectl set env daemonset aws-node \
  -n kube-system \
  ENABLE_PREFIX_DELEGATION=true

# Configure custom networking (pods in different subnets)
kubectl set env daemonset aws-node \
  -n kube-system \
  AWS_VPC_K8S_CNI_CUSTOM_NETWORK_CFG=true
```

## Node Groups

### Managed Node Group with Launch Template

```bash
# Create launch template
aws ec2 create-launch-template \
  --launch-template-name eks-node-template \
  --launch-template-data '{
    "BlockDeviceMappings": [{
      "DeviceName": "/dev/xvda",
      "Ebs": {"VolumeSize": 100, "VolumeType": "gp3", "Encrypted": true}
    }],
    "MetadataOptions": {
      "HttpTokens": "required",
      "HttpEndpoint": "enabled"
    }
  }'

# Create node group with launch template
aws eks create-nodegroup \
  --cluster-name my-cluster \
  --nodegroup-name custom-workers \
  --node-role arn:aws:iam::123456789012:role/eks-node-role \
  --subnets subnet-12345678 subnet-87654321 \
  --launch-template name=eks-node-template,version=1 \
  --scaling-config minSize=1,maxSize=10,desiredSize=3
```

### Spot Instances

```bash
eksctl create nodegroup \
  --cluster my-cluster \
  --name spot-workers \
  --node-type t3.medium,t3.large,t3a.medium,t3a.large \
  --nodes 3 \
  --spot
```

### ARM64 (Graviton)

```bash
aws eks create-nodegroup \
  --cluster-name my-cluster \
  --nodegroup-name graviton-workers \
  --node-role arn:aws:iam::123456789012:role/eks-node-role \
  --subnets subnet-12345678 \
  --ami-type AL2_ARM_64 \
  --instance-types t4g.medium m6g.medium
```

### GPU Nodes

```bash
aws eks create-nodegroup \
  --cluster-name my-cluster \
  --nodegroup-name gpu-workers \
  --node-role arn:aws:iam::123456789012:role/eks-node-role \
  --subnets subnet-12345678 \
  --ami-type AL2_x86_64_GPU \
  --instance-types p3.2xlarge g4dn.xlarge \
  --scaling-config minSize=0,maxSize=5,desiredSize=0
```

## Fargate

### Create Fargate Profile

```bash
# Create pod execution role
aws iam create-role \
  --role-name eks-fargate-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "eks-fargate-pods.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

aws iam attach-role-policy \
  --role-name eks-fargate-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonEKSFargatePodExecutionRolePolicy

# Create Fargate profile
aws eks create-fargate-profile \
  --cluster-name my-cluster \
  --fargate-profile-name default-fargate \
  --pod-execution-role-arn arn:aws:iam::123456789012:role/eks-fargate-role \
  --subnets subnet-private1 subnet-private2 \
  --selectors namespace=default,labels={compute=fargate}
```

### Deploy to Fargate

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: fargate-pod
  labels:
    compute: fargate  # Matches Fargate profile selector
spec:
  containers:
  - name: app
    image: nginx
```

## Cluster Autoscaler

```bash
# Create IRSA for cluster autoscaler
eksctl create iamserviceaccount \
  --cluster my-cluster \
  --namespace kube-system \
  --name cluster-autoscaler \
  --attach-policy-arn arn:aws:iam::123456789012:policy/ClusterAutoscalerPolicy \
  --approve

# Deploy cluster autoscaler
kubectl apply -f https://raw.githubusercontent.com/kubernetes/autoscaler/master/cluster-autoscaler/cloudprovider/aws/examples/cluster-autoscaler-autodiscover.yaml

# Configure for cluster
kubectl -n kube-system annotate deployment cluster-autoscaler \
  cluster-autoscaler.kubernetes.io/safe-to-evict="false"

kubectl -n kube-system set env deployment cluster-autoscaler \
  AWS_REGION=us-east-1 \
  CLUSTER_NAME=my-cluster
```

## Karpenter (Recommended)

```bash
# Install Karpenter
helm install karpenter oci://public.ecr.aws/karpenter/karpenter \
  --namespace karpenter --create-namespace \
  --set settings.clusterName=my-cluster \
  --set settings.clusterEndpoint=$(aws eks describe-cluster --name my-cluster --query "cluster.endpoint" --output text) \
  --set serviceAccount.annotations."eks\.amazonaws\.com/role-arn"=arn:aws:iam::123456789012:role/karpenter-role

# Create NodePool
cat <<EOF | kubectl apply -f -
apiVersion: karpenter.sh/v1beta1
kind: NodePool
metadata:
  name: default
spec:
  template:
    spec:
      requirements:
        - key: kubernetes.io/arch
          operator: In
          values: ["amd64", "arm64"]
        - key: karpenter.sh/capacity-type
          operator: In
          values: ["spot", "on-demand"]
      nodeClassRef:
        name: default
  limits:
    cpu: 1000
  disruption:
    consolidationPolicy: WhenUnderutilized
EOF
```

## Load Balancer Controller

```bash
# Create IRSA
eksctl create iamserviceaccount \
  --cluster my-cluster \
  --namespace kube-system \
  --name aws-load-balancer-controller \
  --attach-policy-arn arn:aws:iam::123456789012:policy/AWSLoadBalancerControllerIAMPolicy \
  --approve

# Install controller
helm install aws-load-balancer-controller \
  eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=my-cluster \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller
```

### Ingress Example

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-ingress
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
spec:
  rules:
  - http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: my-service
            port:
              number: 80
```

## Logging and Monitoring

### Enable Control Plane Logging

```bash
aws eks update-cluster-config \
  --name my-cluster \
  --logging '{
    "clusterLogging": [{
      "types": ["api", "audit", "authenticator", "controllerManager", "scheduler"],
      "enabled": true
    }]
  }'
```

### Container Insights

```bash
# Install CloudWatch agent and Fluent Bit
curl https://raw.githubusercontent.com/aws-samples/amazon-cloudwatch-container-insights/latest/k8s-deployment-manifest-templates/deployment-mode/daemonset/container-insights-monitoring/quickstart/cwagent-fluent-bit-quickstart.yaml | \
  sed "s/{{cluster_name}}/my-cluster/g; s/{{region_name}}/us-east-1/g" | \
  kubectl apply -f -
```

## Security

### Secrets Encryption

```bash
# Create KMS key
aws kms create-key --description "EKS secrets encryption"

# Enable encryption
aws eks create-cluster \
  --name my-cluster \
  --encryption-config '[{
    "provider": {"keyArn": "arn:aws:kms:us-east-1:123456789012:key/..."},
    "resources": ["secrets"]
  }]' \
  ...
```

### Security Groups for Pods

```bash
# Enable security groups for pods
aws eks update-cluster-config \
  --name my-cluster \
  --resources-vpc-config \
    endpointPublicAccess=true,\
    endpointPrivateAccess=true,\
    securityGroupIds=sg-12345678

# Annotate node group
kubectl annotate node <node> \
  vpc.amazonaws.com/pod-eni=enabled
```
