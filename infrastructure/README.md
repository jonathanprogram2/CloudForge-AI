# CloudForge AI — AWS Infrastructure

## Overview

CloudForge AI is an AI benchmarking and operations platform
built with FastAPI, React, Docker, and Terraform.

This infrastructure project defines an AWS container
deployment using Infrastructure as Code.

## AWS Architecture

- Amazon VPC: Isolated application networking
- Public Subnets: Two availability zones
- Internet Gateway: Internet connectivity
- Application Load Balancer: HTTP traffic routing
- Amazon ECS Fargate: Containerized FastAPI backend
- Amazon ECR: Docker image repository
- AWS IAM: ECS execution and application roles
- Amazon CloudWatch: Container logging

## Infrastructure Validation

Run these commands inside infrastructure/terraform:

    terraform fmt -check -recursive
    terraform init -backend=false
    terraform validate

These checks do not provision AWS resources.

## Continuous Integration

GitHub Actions automatically runs:

1. Python backend tests
2. Frontend linting and production build
3. Terraform formatting and validation
4. Infrastructure security scanning
5. Docker image vulnerability scanning

## Security Considerations

The initial architecture uses public subnets for ECS
and an HTTP load balancer to simplify learning.

Before production use, improvements should include:

- HTTPS with ACM certificates
- Private ECS subnets
- Restricted network access
- Persistent database storage
- Secrets management
- Least-privilege IAM policies
- CloudWatch alarms
- Authentication and authorization
- AWS cost monitoring

## Deployment Status

Infrastructure is defined and locally validated.

Real AWS deployment and load testing have not yet
been performed.

Do not run terraform apply without reviewing costs
and replacing the placeholder container image.

## Cost Strategy

Development and Terraform validation happen locally.

AWS deployment is optional and must be reviewed
for pricing before provisioning billable resources.
