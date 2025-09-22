# Staging Environment

This overlay configures the application for the staging environment, providing a production-like setup for testing and validation.

## Overview

The staging overlay extends the base configuration with environment-specific customizations:

- **Namespace**: Resources are deployed to the `staging` namespace
- **Replicas**: Runs 2 replicas for load testing
- **Image Tag**: Uses `nginx:1.21-staging` for pre-production testing
- **Resource Limits**: Applied moderate resource constraints for realistic testing
- **Configuration**: Staging-specific database connections and logging

## Key Differences from Base

### Scaling
- **Replica Count**: 2 instances (vs 1 in base)
- **Resource Requests**: Moderate CPU/memory allocation
- **Resource Limits**: Enforced limits for stability testing

### Configuration
- **Database**: Points to staging PostgreSQL instance
- **Logging**: Info level logging for debugging
- **Environment Variables**: Staging-specific configuration values

### Naming
- **Name Prefix**: All resources prefixed with `staging-`
- **Labels**: Tagged with `environment: staging`
- **Namespace**: Deployed to dedicated `staging` namespace

## Patches Applied

This overlay applies several patches:
- `replica-patch.yaml` - Adjusts replica count and scaling behavior
- `resource-patch.yaml` - Sets appropriate resource requests and limits

## Usage

This environment is used for:
- **Integration Testing**: Full application stack testing
- **Performance Validation**: Load and stress testing
- **User Acceptance Testing**: Stakeholder review and approval
- **Deployment Validation**: Testing deployment procedures

## Database Configuration

Connects to the staging database cluster:
- **Host**: `staging-db:5432`
- **Database**: `app`
- **Connection Pooling**: Enabled for performance testing

## Monitoring

The staging environment includes:
- Application performance monitoring
- Resource usage tracking
- Error rate monitoring
- Response time measurement