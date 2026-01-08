---
name: eks
description: AWS EKS Kubernetes management for clusters, node groups, and workloads. Use when creating clusters, configuring IRSA, managing node groups, deploying applications, or integrating with AWS services.
last_updated: "2026-01-07"
doc_source: https://docs.aws.amazon.com/eks/latest/userguide/
---

# AWS EKS

Amazon Elastic Kubernetes Service (EKS) runs Kubernetes without installing and operating your own control plane. EKS manages the control plane and integrates with AWS services.

## Table of Contents

- [Core Concepts](#core-concepts)
- [Common Patterns](#common-patterns)
- [CLI Reference](#cli-reference)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [References](#references)

## Core Concepts

### Control Plane

Managed by AWS. Runs Kubernetes API server, etcd, and controllers across multiple AZs.

### Node Groups

| Type | Description |
|------|-------------|
| **Managed** | AWS manages provisioning, updates |
| **Self-managed** | You manage EC2 instances |
| **Fargate** | Serverless, per-pod compute |

### IRSA (IAM Roles for Service Accounts)

Associates Kubernetes service accounts with IAM roles for fine-grained AWS permissions.

### Add-ons

Operational software: CoreDNS, kube-proxy, VPC CNI, EBS CSI driver.

## Common Patterns

### Create a Cluster

**AWS CLI:**

```bash
# Create cluster role
aws iam create-role \
  --role-name eks-cluster-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "eks.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

aws iam attach-role-policy \
  --role-name eks-cluster-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonEKSClusterPolicy

# Create cluster
aws eks create-cluster \
  --name my-cluster \
  --role-arn arn:aws:iam::123456789012:role/eks-cluster-role \
  --resources-vpc-config subnetIds=subnet-12345678,subnet-87654321,securityGroupIds=sg-12345678

# Wait for cluster
aws eks wait cluster-active --name my-cluster

# Update kubeconfig
aws eks update-kubeconfig --name my-cluster --region us-east-1
```

**eksctl (Recommended):**

```bash
# Create cluster with managed node group
eksctl create cluster \
  --name my-cluster \
  --region us-east-1 \
  --version 1.29 \
  --nodegroup-name standard-workers \
  --node-type t3.medium \
  --nodes 3 \
  --nodes-min 1 \
  --nodes-max 5 \
  --managed
```

### Add Managed Node Group

```bash
# Create node role
aws iam create-role \
  --role-name eks-node-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "ec2.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

aws iam attach-role-policy --role-name eks-node-role --policy-arn arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy
aws iam attach-role-policy --role-name eks-node-role --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly
aws iam attach-role-policy --role-name eks-node-role --policy-arn arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy

# Create node group
aws eks create-nodegroup \
  --cluster-name my-cluster \
  --nodegroup-name standard-workers \
  --node-role arn:aws:iam::123456789012:role/eks-node-role \
  --subnets subnet-12345678 subnet-87654321 \
  --instance-types t3.medium \
  --scaling-config minSize=1,maxSize=5,desiredSize=3 \
  --ami-type AL2_x86_64
```

### Configure IRSA

```bash
# Enable OIDC provider
eksctl utils associate-iam-oidc-provider \
  --cluster my-cluster \
  --approve

# Create IAM role for service account
eksctl create iamserviceaccount \
  --cluster my-cluster \
  --namespace default \
  --name my-app-sa \
  --attach-policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess \
  --approve
```

**Manual IRSA setup:**

```bash
# Get OIDC issuer
OIDC_ISSUER=$(aws eks describe-cluster --name my-cluster --query "cluster.identity.oidc.issuer" --output text)
OIDC_ID=${OIDC_ISSUER##*/}

# Create trust policy
cat > trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {
      "Federated": "arn:aws:iam::123456789012:oidc-provider/oidc.eks.us-east-1.amazonaws.com/id/${OIDC_ID}"
    },
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {
      "StringEquals": {
        "oidc.eks.us-east-1.amazonaws.com/id/${OIDC_ID}:sub": "system:serviceaccount:default:my-app-sa",
        "oidc.eks.us-east-1.amazonaws.com/id/${OIDC_ID}:aud": "sts.amazonaws.com"
      }
    }
  }]
}
EOF

aws iam create-role --role-name my-app-role --assume-role-policy-document file://trust-policy.json
```

### Kubernetes Service Account

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: my-app-sa
  namespace: default
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::123456789012:role/my-app-role
```

### Install Add-ons

```bash
# CoreDNS
aws eks create-addon \
  --cluster-name my-cluster \
  --addon-name coredns \
  --addon-version v1.11.1-eksbuild.4

# VPC CNI
aws eks create-addon \
  --cluster-name my-cluster \
  --addon-name vpc-cni \
  --addon-version v1.16.0-eksbuild.1

# kube-proxy
aws eks create-addon \
  --cluster-name my-cluster \
  --addon-name kube-proxy \
  --addon-version v1.29.0-eksbuild.1

# EBS CSI Driver
aws eks create-addon \
  --cluster-name my-cluster \
  --addon-name aws-ebs-csi-driver \
  --addon-version v1.27.0-eksbuild.1 \
  --service-account-role-arn arn:aws:iam::123456789012:role/ebs-csi-role
```

### Deploy Application

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      serviceAccountName: my-app-sa
      containers:
      - name: app
        image: 123456789012.dkr.ecr.us-east-1.amazonaws.com/my-app:latest
        ports:
        - containerPort: 8080
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 512Mi
---
apiVersion: v1
kind: Service
metadata:
  name: my-app
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: nlb
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 8080
  selector:
    app: my-app
```

## CLI Reference

### Cluster Management

| Command | Description |
|---------|-------------|
| `aws eks create-cluster` | Create cluster |
| `aws eks describe-cluster` | Get cluster details |
| `aws eks update-cluster-config` | Update cluster settings |
| `aws eks delete-cluster` | Delete cluster |
| `aws eks update-kubeconfig` | Configure kubectl |

### Node Groups

| Command | Description |
|---------|-------------|
| `aws eks create-nodegroup` | Create node group |
| `aws eks describe-nodegroup` | Get node group details |
| `aws eks update-nodegroup-config` | Update node group |
| `aws eks delete-nodegroup` | Delete node group |

### Add-ons

| Command | Description |
|---------|-------------|
| `aws eks create-addon` | Install add-on |
| `aws eks describe-addon` | Get add-on details |
| `aws eks update-addon` | Update add-on |
| `aws eks delete-addon` | Remove add-on |

## Best Practices

### Security

- **Use IRSA** for pod-level AWS permissions
- **Enable cluster encryption** with KMS
- **Use private endpoint** for API server
- **Enable audit logging** to CloudWatch
- **Use security groups for pods**
- **Implement network policies**

```bash
# Enable secrets encryption
aws eks create-cluster \
  --name my-cluster \
  --encryption-config '[{
    "provider": {"keyArn": "arn:aws:kms:us-east-1:123456789012:key/..."},
    "resources": ["secrets"]
  }]' \
  ...
```

### High Availability

- **Deploy across multiple AZs**
- **Use managed node groups**
- **Set pod disruption budgets**
- **Configure horizontal pod autoscaling**

### Cost Optimization

- **Use Spot instances** for non-critical workloads
- **Right-size nodes and pods**
- **Use Fargate** for variable workloads
- **Implement cluster autoscaler**
- **Use Karpenter** for efficient scaling

## Troubleshooting

### Cannot Connect to Cluster

```bash
# Verify kubeconfig
aws eks update-kubeconfig --name my-cluster --region us-east-1

# Check IAM identity
aws sts get-caller-identity

# Verify cluster status
aws eks describe-cluster --name my-cluster --query 'cluster.status'
```

### Nodes Not Joining

**Check:**
- Node IAM role has required policies
- Security groups allow node-to-control-plane communication
- Nodes have network access to API server

```bash
# Check node status
kubectl get nodes

# Check aws-auth ConfigMap
kubectl describe configmap aws-auth -n kube-system

# Check node logs (SSH to node)
journalctl -u kubelet
```

### Pod Cannot Access AWS Services

```bash
# Verify IRSA setup
kubectl describe sa my-app-sa

# Check pod environment
kubectl exec my-pod -- env | grep AWS

# Test credentials
kubectl exec my-pod -- aws sts get-caller-identity
```

### DNS Issues

```bash
# Check CoreDNS pods
kubectl get pods -n kube-system -l k8s-app=kube-dns

# Test DNS resolution
kubectl run test --image=busybox:1.28 --rm -it -- nslookup kubernetes

# Check CoreDNS logs
kubectl logs -n kube-system -l k8s-app=kube-dns
```

## References

- [EKS User Guide](https://docs.aws.amazon.com/eks/latest/userguide/)
- [EKS API Reference](https://docs.aws.amazon.com/eks/latest/APIReference/)
- [EKS CLI Reference](https://docs.aws.amazon.com/cli/latest/reference/eks/)
- [eksctl](https://eksctl.io/)
- [EKS Best Practices Guide](https://aws.github.io/aws-eks-best-practices/)
