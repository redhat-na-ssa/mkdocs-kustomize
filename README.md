# MkDocs Kustomize Plugin

A MkDocs plugin that integrates [Kustomize](https://kustomize.io/) functionality into your documentation.

## Features

- **Auto-Discovery**: Automatically discover and document all Kustomize directories in your project
- **Resource Analysis**: Interactive table with expandable YAML content for each Kubernetes resource
- **Manual Integration**: Render Kustomize manifests directly in your documentation pages
- **YAML Overrides**: Apply inline overrides to Kustomize outputs in your documentation
- **Built-in Syntax Highlighting**: Uses MkDocs' integrated syntax highlighting for all YAML content
- **Navigation Integration**: Automatically adds discovered Kustomize configurations to your site navigation

## Installation

```bash
pip install mkdocs-kustomize
```

Alternatively, you can install directly from the git repository:

```bash
pip install git+https://github.com/yourusername/mkdocs-kustomize.git
```

## Quick Start

### Basic Configuration

Add the plugin to your `mkdocs.yml`:

```yaml
plugins:
  - search
  - kustomize:
      enable_rendering: true
```

### Auto-Discovery Configuration

For automatic discovery and documentation of all your Kustomize configurations:

```yaml
plugins:
  - search
  - kustomize:
      auto_nav_path: "kubernetes/"    # Path to scan for kustomization.yaml files
      nav_title: "Infrastructure"     # Navigation section title
      enable_rendering: true
```

### Full Configuration Options

```yaml
plugins:
  - search
  - kustomize:
      kustomize_path: kustomize       # Path to the kustomize binary (default: "kustomize")
      kustomize_dirs:                 # Base directories for manual integration
        - kubernetes/
        - k8s/
      enable_rendering: true          # Enable/disable plugin (default: true)
      auto_nav_path: "kubernetes/"    # Auto-discover path (default: disabled)
      nav_title: "Infrastructure"     # Auto-generated navigation title
```

## Usage

### Auto-Discovery (Recommended)

The easiest way to get started is with auto-discovery. Point the plugin to your Kubernetes/Kustomize directory:

```yaml
plugins:
  - kustomize:
      auto_nav_path: "kubernetes/"  # Path containing your kustomization directories
      nav_title: "Infrastructure"   # Navigation section title
```

This will automatically:
- 🔍 **Recursively Discover** all directories with `kustomization.yaml` files (no matter how deeply nested)
- 📄 **Generate** documentation pages for each configuration  
- 📝 **Include** README.md content from each directory
- 📊 **Analyze** all Kubernetes resources with expandable YAML
- 🧭 **Add** everything to your site navigation with proper hierarchy

#### Directory Structure Example (Recursive Discovery)
```
kubernetes/
├── base/
│   ├── kustomization.yaml          # ← Discovered
│   ├── README.md                   # ← Content included
│   └── ...
├── overlays/
│   ├── staging/
│   │   ├── kustomization.yaml      # ← Discovered
│   │   ├── README.md               # ← Content included
│   │   └── ...
│   └── production/
│       ├── kustomization.yaml      # ← Discovered
│       ├── README.md               # ← Content included
│       └── ...
├── components/
│   └── monitoring/
│       └── prometheus/
│           ├── kustomization.yaml  # ← Discovered (deeply nested)
│           └── README.md           # ← Content included
└── apps/
    ├── frontend/
    │   ├── base/
    │   │   ├── kustomization.yaml  # ← Discovered
    │   │   └── README.md           # ← Content included
    │   └── overlays/
    │       └── dev/
    │           ├── kustomization.yaml  # ← Discovered
    │           └── README.md       # ← Content included
    └── backend/
        ├── kustomization.yaml      # ← Discovered
        └── README.md               # ← Content included
```

Results in navigation (ALL directories discovered recursively):
- **Infrastructure**
  - Base
  - Overlays > Staging  
  - Overlays > Production
  - Components > Monitoring > Prometheus
  - Apps > Frontend > Base
  - Apps > Frontend > Overlays > Dev
  - Apps > Backend

### Manual Integration

For more control, you can manually embed Kustomize configurations in your documentation:

#### Basic Usage

````markdown
```kustomize path/to/kustomize/dir
```
````

#### With Resource Analysis

````markdown
```kustomize path/to/kustomize/dir [analyze=true]
```
````

#### With YAML Overrides

````markdown
```kustomize path/to/kustomize/dir
kind: Deployment
metadata:
  name: my-deployment
spec:
  replicas: 5  # Override the replica count
```
````

### Resource Analysis

You can enable analysis of Kubernetes resources by adding the `analyze=true` option:

````markdown
```kustomize path/to/kustomize/dir [analyze=true]
```
````

This will generate a compact table showing details about each resource with expandable YAML content:

![Resource Table Example](https://via.placeholder.com/600x300?text=Compact+Resource+Table+With+Expandable+YAML)

Each resource row includes a "▼ YAML" button that expands to show the complete YAML for that specific resource directly beneath the row, making it easier to browse complex manifests while keeping the documentation clean. The button changes to "▲ YAML" when expanded.

The table includes:
- Kind (with API Group/Version as smaller text below)
- Name
- Namespace (empty if not defined in the YAML)
- YAML button to expand/collapse the resource definition with MkDocs built-in syntax highlighting

This compact design helps save horizontal space in the documentation while still providing all the necessary information with enhanced readability through MkDocs' integrated syntax highlighting. The namespace column displays only the actual namespace from the YAML metadata, remaining empty for cluster-scoped resources or resources without an explicit namespace.

## Requirements

- Python 3.6+
- MkDocs 1.1.0+
- Kustomize installed and accessible in PATH (or configured path)

## Development

To set up the development environment:

```bash
git clone https://github.com/yourusername/mkdocs-kustomize.git
cd mkdocs-kustomize
pip install -e .
```

## License

MIT