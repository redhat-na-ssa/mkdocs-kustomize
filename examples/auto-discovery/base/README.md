# Base Configuration

This directory contains the base Kustomize configuration for our example application.

## Overview

The base configuration defines the core Kubernetes resources that are common across all environments:

- **Deployment**: Core application deployment with nginx container
- **Service**: ClusterIP service to expose the application internally
- **ConfigMap**: Application configuration that can be customized per environment

## Resources

This base includes:

- `deployment.yaml` - Main application deployment
- `service.yaml` - Service definition for internal communication
- `configmap.yaml` - Configuration data for the application

## Common Labels

All resources in this base are tagged with:
- `app: example-app`
- `environment: base`

## Image Configuration

The base uses nginx:1.21 as the default image, which can be overridden in overlays for different environments.

## Usage

This base is designed to be used with overlays for specific environments like staging and production. It provides the foundation that other configurations can build upon.