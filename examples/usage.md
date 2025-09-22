# MkDocs Kustomize Plugin Usage

This document demonstrates how to use the MkDocs Kustomize plugin to render Kubernetes resources directly in your documentation.

## Basic Usage

The simplest way to use the plugin is to reference a directory containing a `kustomization.yaml` file:

````markdown
```kustomize path/to/examples
```
````

This will render the output of `kustomize build path/to/examples` as YAML in your documentation.

## Using Overrides

You can also provide inline YAML to override specific parts of the resources:

````markdown
```kustomize path/to/examples
kind: Deployment
metadata:
  name: demo-example-deployment
spec:
  replicas: 5
```
````

The above example would override the number of replicas in the rendered output.

## Resource Analysis

You can enable analysis of Kubernetes resources by adding the `analyze=true` option to your kustomize block:

````markdown
```kustomize path/to/examples [analyze=true]
```
````

This will render a table showing information about each resource with expandable YAML content directly under each row:

<div class='mkdocs-kustomize-plugin resource-analysis'>
<table class='resource-table'>
  <thead>
    <tr>
      <th>Kind</th>
      <th>Name</th>
      <th>Namespace</th>
      <th>Details</th>
    </tr>
  </thead>
  <tbody>
    <tr class='resource-row'>
      <td>Deployment<span class="resource-api-info">apps/v1</span></td>
      <td>demo-example-deployment</td>
      <td>default</td>
      <td><input type="checkbox" id="resource-1-check" class="k8s-yaml-checkbox" aria-label="Show YAML for Deployment demo-example-deployment" /><label for="resource-1-check" class="k8s-yaml-toggle">▼ YAML</label></td>
    </tr>
    <tr id="resource-1-row" class="k8s-yaml-row k8s-yaml-expanded" data-yaml-id="resource-1">
      <td colspan="4">
        <div class="resource-details">

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: demo-example-deployment
  namespace: default
  labels:
    app: example-app
    environment: dev
spec:
  replicas: 2
  selector:
    matchLabels:
      app: example-app
      environment: dev
  template:
    metadata:
      labels:
        app: example-app
        environment: dev
    spec:
      containers:
      - name: example-container
        image: nginx:1.21
```

        </div>
      </td>
    </tr>
    <tr class='resource-row'>
      <td>Service<span class="resource-api-info">v1</span></td>
      <td>demo-example-service</td>
      <td></td>
      <td><input type="checkbox" id="resource-2-check" class="k8s-yaml-checkbox" aria-label="Show YAML for Service demo-example-service" /><label for="resource-2-check" class="k8s-yaml-toggle">▼ YAML</label></td>
    </tr>
    <tr id="resource-2-row" class="k8s-yaml-row" data-yaml-id="resource-2">
      <td colspan="4">
        <div class="resource-details">

```yaml
apiVersion: v1
kind: Service
metadata:
  name: demo-example-service
spec:
  selector:
    app: example-app
  ports:
  - port: 80
    targetPort: 80
```

        </div>
      </td>
    </tr>
  </tbody>
</table>
</div>

<p><em>Note: The first row is shown expanded for demonstration purposes. In the actual plugin implementation, all rows start collapsed and expand when the "▼ YAML" button is clicked (which changes to "▲ YAML" when expanded). The implementation uses a checkbox-based toggling mechanism that works even when JavaScript is disabled, providing maximum compatibility across browsers and environments. API group and version information is shown in smaller text below the Kind for a more compact table layout. The YAML content uses MkDocs' built-in syntax highlighting. Namespace cells are left empty when no namespace is defined in the YAML.</em></p>

## Example Output

Here's what the rendered output might look like:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: demo-example-service
  labels:
    app: example-app
    environment: dev
spec:
  selector:
    app: example-app
    environment: dev
  ports:
  - port: 80
    targetPort: 80
    name: http
  type: ClusterIP
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: demo-example-deployment
  labels:
    app: example-app
    environment: dev
spec:
  replicas: 2
  selector:
    matchLabels:
      app: example-app
      environment: dev
  template:
    metadata:
      labels:
        app: example-app
        environment: dev
    spec:
      containers:
      - name: example-container
        image: nginx:1.21
        ports:
        - containerPort: 80
        resources:
          limits:
            cpu: "0.5"
            memory: "512Mi"
          requests:
            cpu: "0.1"
            memory: "128Mi"
        env:
        - name: DATABASE_URL
          valueFrom:
            configMapKeyRef:
              name: demo-app-config
              key: DATABASE_URL
        - name: API_KEY
          valueFrom:
            configMapKeyRef:
              name: demo-app-config
              key: API_KEY
        - name: ENVIRONMENT
          valueFrom:
            configMapKeyRef:
              name: demo-app-config
              key: ENVIRONMENT
        livenessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: demo-app-config
  labels:
    app: example-app
    environment: dev
data:
  API_KEY: example-key
  DATABASE_URL: postgres://user:password@postgres-service:5432/db
  ENVIRONMENT: development
```

## Configuration in mkdocs.yml

To enable this plugin, add the following to your `mkdocs.yml`:

```yaml
plugins:
  - search
  - kustomize:
      kustomize_path: kustomize
      kustomize_dirs:
        - kubernetes/
        - k8s/
      enable_rendering: true
      auto_nav_path: "kubernetes/"  # Optional: auto-discover kustomize directories
      nav_title: "Infrastructure"   # Title for auto-generated navigation
```

### Auto-Discovery Configuration

When `auto_nav_path` is set, the plugin will:

1. **Recursively Scan**: Deep search through ALL subdirectories for any `kustomization.yaml` or `kustomization.yml` files
2. **Auto-Generate Pages**: Create documentation pages for each discovered Kustomize directory, no matter how deeply nested
3. **Include README Content**: If a `README.md` exists in any kustomize directory, its content will be included
4. **Add Resource Analysis**: Each page will include a resource analysis table with the `analyze=true` option enabled

Example directory structure (showing recursive discovery):
```
kubernetes/
├── base/
│   ├── kustomization.yaml          # ← Discovered
│   └── README.md
├── overlays/
│   ├── production/
│   │   ├── kustomization.yaml      # ← Discovered
│   │   └── README.md
│   └── staging/
│       ├── kustomization.yaml      # ← Discovered
│       └── README.md
├── components/
│   └── monitoring/
│       └── prometheus/
│           ├── kustomization.yaml  # ← Discovered (deeply nested)
│           └── README.md
└── apps/
    ├── frontend/
    │   ├── base/
    │   │   ├── kustomization.yaml  # ← Discovered
    │   │   └── README.md
    │   └── overlays/
    │       └── dev/
    │           ├── kustomization.yaml  # ← Discovered
    │           └── README.md
    └── backend/
        ├── kustomization.yaml      # ← Discovered
        └── README.md
```

This will automatically create navigation for ALL discovered directories:
- Infrastructure > Base
- Infrastructure > Overlays > Production  
- Infrastructure > Overlays > Staging
- Infrastructure > Components > Monitoring > Prometheus
- Infrastructure > Apps > Frontend > Base
- Infrastructure > Apps > Frontend > Overlays > Dev
- Infrastructure > Apps > Backend

Each page will show the README content followed by the kustomize resource analysis.

## Requirements

- Kustomize must be installed and available in your PATH
- Python 3.6+
- MkDocs 1.1.0+

## Options

The plugin supports the following options in the markdown code blocks:

```
```kustomize path/to/examples [options]
```
```

Available options:
- `analyze=true` - Enables resource analysis table with button-style expandable YAML content using MkDocs built-in syntax highlighting