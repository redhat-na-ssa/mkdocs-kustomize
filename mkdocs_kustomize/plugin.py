import os
import subprocess
import logging
import yaml
from mkdocs.plugins import BasePlugin
from mkdocs.config import config_options
from mkdocs.structure.files import File
from mkdocs.structure.pages import Page

log = logging.getLogger('mkdocs.plugins.kustomize')

class KustomizePlugin(BasePlugin):
    """
    MkDocs plugin for integrating Kustomize functionality.

    This plugin allows you to integrate Kustomize with your MkDocs documentation,
    enabling you to render Kubernetes manifests directly in your docs.
    """

    config_scheme = (
        ('kustomize_path', config_options.Type(str, default='kustomize')),
        ('kustomize_dirs', config_options.Type(list, default=[])),
        ('enable_rendering', config_options.Type(bool, default=True)),
        ('auto_nav_path', config_options.Type(str, default='')),
        ('nav_title', config_options.Type(str, default='Kustomize')),
    )

    def __init__(self):
        super().__init__()
        # Store mapping of relative paths to absolute paths for auto-discovered directories
        self._kustomize_path_mapping = {}
        self.global_config = None

    def _extract_title_from_readme(self, content):
        """
        Extract title from README.md content by finding the first # heading.
        Handles code blocks properly to avoid extracting titles from within them.

        Args:
            content: String content of README.md file

        Returns:
            String title or None if no title found
        """
        if not content:
            return None

        lines = content.split('\n')
        in_code_block = False

        for line in lines:
            stripped_line = line.strip()

            # Track code block boundaries
            if stripped_line.startswith('```'):
                in_code_block = not in_code_block
                continue

            # Skip lines inside code blocks
            if in_code_block:
                continue

            # Look for level 1 heading outside of code blocks
            if stripped_line.startswith('# ') and len(stripped_line) > 2:
                return stripped_line[2:].strip()

        return None

    def on_config(self, config):
        """
        Called when the MkDocs config is loaded.

        Args:
            config: Global configuration object

        Returns:
            Configuration object
        """
        # Verify kustomize is installed if plugin is enabled
        if self.config['enable_rendering']:
            try:
                _ = subprocess.run(
                    ['kustomize', 'version'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True
                )
                log.info("Kustomize detected and working.")
            except (subprocess.SubprocessError, FileNotFoundError):
                log.warning("Kustomize not found or not working. Plugin functionality will be limited.")

        self.global_config = config
        return config

    def on_files(self, files, config):
        """
        Called after the files collection is populated from the docs_dir.
        This is where we can add auto-discovered kustomize pages.
        """
        if not self.config['auto_nav_path'] or not self.config['enable_rendering']:
            return files

        # Discover kustomize directories and create pages
        auto_nav_path = self.config['auto_nav_path']
        if not os.path.isabs(auto_nav_path):
            auto_nav_path = os.path.join(auto_nav_path)

        log.info(f"Scanning for kustomization files in: {auto_nav_path}")

        if os.path.exists(auto_nav_path):
            kustomize_dirs = self._find_kustomize_directories(auto_nav_path)

            # Create index page for the Infrastructure section
            index_page_path = f"kustomize/index.md"
            index_virtual_file = File(
                index_page_path,
                config['docs_dir'],
                config['site_dir'],
                config['use_directory_urls']
            )
            index_virtual_file.content_string = self._generate_index_page_content(kustomize_dirs)
            files.append(index_virtual_file)

            # Create virtual pages for each kustomize directory
            for kustomize_dir in kustomize_dirs:
                rel_path = os.path.relpath(kustomize_dir, auto_nav_path)
                # Normalize path separators and create page path
                normalized_path = rel_path.replace(os.sep, '/')
                page_path = f"kustomize/{normalized_path}.md"

                # Store mapping for later path resolution
                self._kustomize_path_mapping[normalized_path] = kustomize_dir

                # Create a virtual file for this kustomize directory
                virtual_file = File(
                    page_path,
                    config['docs_dir'],
                    config['site_dir'],
                    config['use_directory_urls']
                )
                virtual_file.content_string = self._generate_kustomize_page_content(kustomize_dir, normalized_path)
                files.append(virtual_file)

        return files

    def on_nav(self, nav, config, files):
        """
        Called after the site navigation is created.
        This is where we can modify the navigation to include our auto-discovered pages.
        """
        if not self.config['auto_nav_path'] or not self.config['enable_rendering']:
            return nav

        # Find kustomize pages and create Page objects
        index_page = None
        kustomize_pages = []

        for file in files:
            if file.src_path.startswith('kustomize/') and file.src_path.endswith('.md'):
                page = Page(None, file, config)

                if file.src_path == 'kustomize/index.md':
                    # This is the index page
                    page.title = self.config['nav_title']
                    page.read_source(config)  # Initialize page content
                    index_page = page
                else:
                    # Extract title from actual README.md file adjacent to kustomization.yaml
                    page.read_source(config)  # Initialize page content first

                    # Get the relative path and find the corresponding kustomize directory
                    rel_path = file.src_path[10:-3]  # Remove 'kustomize/' and '.md'

                    # Look up the actual kustomize directory from our mapping
                    readme_title = None
                    if rel_path in self._kustomize_path_mapping:
                        kustomize_dir = self._kustomize_path_mapping[rel_path]
                        readme_path = os.path.join(kustomize_dir, 'README.md')

                        if os.path.exists(readme_path):
                            try:
                                with open(readme_path, 'r', encoding='utf-8') as f:
                                    readme_content = f.read()
                                    readme_title = self._extract_title_from_readme(readme_content)
                                    log.info(f"Extracted title '{readme_title}' from {readme_path} for rel_path '{rel_path}'")
                            except Exception as e:
                                log.warning(f"Could not read README.md from {readme_path}: {e}")
                        else:
                            log.warning(f"README.md not found at {readme_path} for rel_path '{rel_path}'")

                    # Use README title if found, otherwise fall back to directory name
                    if readme_title:
                        page.title = readme_title
                        log.info(f"Set page title to '{page.title}' from README for {file.src_path}")
                    else:
                        page.title = rel_path.replace('/', ' > ').replace('_', ' ').replace('-', ' ').title()
                        log.info(f"Set page title to '{page.title}' from directory name for {file.src_path}")
                    kustomize_pages.append(page)

        if kustomize_pages:
            # Sort pages by path
            kustomize_pages.sort(key=lambda x: x.file.src_path)

            # Try creating a Section object like the existing navigation
            from mkdocs.structure.nav import Section

            # Create navigation items with index page first
            nav_items = []
            if index_page:
                nav_items.append(index_page)
            nav_items.extend(kustomize_pages)

            # Create Section object
            infrastructure_section = Section(self.config['nav_title'], nav_items)

            # Set up proper parent-child relationships for active state propagation
            for item in nav_items:
                if hasattr(item, 'parent'):
                    item.parent = infrastructure_section

            try:
                if hasattr(nav, 'items'):
                    nav.items.append(infrastructure_section)
                elif isinstance(nav, list):
                    nav.append(infrastructure_section)
                else:
                    log.error(f"Cannot append to navigation of type: {type(nav)}")
                    return nav
            except Exception as e:
                log.error(f"Error appending to navigation: {e}")
                return nav

        return nav

    def _find_kustomize_directories(self, base_path):
        """
        Find directories containing kustomization.yaml files.
        """
        kustomize_dirs = []

        # Walk through all directories and subdirectories
        for root, dirs, files in os.walk(base_path):
            # Check if current directory contains kustomization files
            if ('kustomization.yaml' in files or 'kustomization.yml' in files) and (
                'README.md' in files):
                kustomize_dirs.append(root)

        log.info(f"Discovered {len(kustomize_dirs)} kustomize directories in {base_path}")
        return kustomize_dirs

    def _generate_kustomize_page_content(self, kustomize_dir, rel_path):
        """
        Generate markdown content for a kustomize directory page.
        """
        dir_name = os.path.basename(kustomize_dir)
        content = []

        # Add README content if it exists
        readme_path = os.path.join(kustomize_dir, 'README.md')
        if os.path.exists(readme_path):
            try:
                with open(readme_path, 'r', encoding='utf-8') as f:
                    readme_content = f.read()
                    content.append(readme_content)
                    content.append('\n')
            except Exception as e:
                log.warning(f"Could not read README.md from {readme_path}: {e}")

        # Add kustomize analysis using the relative path (will be resolved via mapping)
        # content.append(f"\n## Kustomize Configuration\n")
        usage_doc = f"""
## Usage

If you have cloned the `gitops-catalog` repository, you can install by running from the root directory:

```sh
oc apply -k {kustomize_dir}
```

Or, without cloning:

```sh
oc apply -k {self.global_config['repo_url']}/{kustomize_dir}
```

As part of a different overlay in your own GitOps repo:

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
    - {self.global_config['repo_url']}/{kustomize_dir}?ref=main
```
"""
        content.append(f"{usage_doc}\n")
        content.append(f"```kustomize {rel_path} [analyze=true]\n```\n")

        return '\n'.join(content)

    def _generate_index_page_content(self, kustomize_dirs):
        """
        Generate markdown content for the Infrastructure index page.
        """
        content = [f"# {self.config['nav_title']}\n"]
        content.append("This section contains auto-discovered Kustomize configurations.\n")
        content.append(f"Found {len(kustomize_dirs)} directories with Kustomize configurations:\n")

        for kustomize_dir in sorted(kustomize_dirs):
            dir_name = os.path.basename(kustomize_dir)
            rel_path = os.path.relpath(kustomize_dir, os.path.dirname(kustomize_dirs[0]) if kustomize_dirs else '')

            # Try to extract title from README.md
            readme_title = None
            readme_path = os.path.join(kustomize_dir, 'README.md')
            if os.path.exists(readme_path):
                try:
                    with open(readme_path, 'r', encoding='utf-8') as f:
                        readme_content = f.read()
                        readme_title = self._extract_title_from_readme(readme_content)
                except Exception as e:
                    log.warning(f"Could not read README.md from {readme_path}: {e}")

            # Use README title if found, otherwise fall back to directory name
            display_title = readme_title if readme_title else dir_name.replace('_', ' ').replace('-', ' ').title()
            content.append(f"- **{display_title}** (`{rel_path}`)")

        content.append("\nUse the navigation menu to explore each configuration.")

        return '\n'.join(content)

    def on_page_markdown(self, markdown, page, config, files):
        """
        Called on each page's markdown content.

        This is where we can look for special tags and replace them with
        rendered Kustomize output.

        Args:
            markdown: Current page markdown as string
            page: Current page instance
            config: Global configuration object
            files: Collection of files in the docs

        Returns:
            Modified markdown
        """
        if not self.config['enable_rendering']:
            return markdown

        import re

        # Look for kustomize code blocks with the format:
        # ```kustomize path/to/kustomize/dir [analyze=true]
        # ... optional yaml override content ...
        # ```
        pattern = r'```kustomize\s+([^[\n]+)(?:\s+\[([^\]]+)\])?\n(.*?)```'

        def replace_match(match):
            kustomize_dir = match.group(1).strip()
            options = {}
            if match.group(2):
                for option in match.group(2).split(','):
                    if '=' in option:
                        key, value = option.split('=', 1)
                        options[key.strip()] = value.strip().lower() == 'true'
                    else:
                        options[option.strip()] = True
            override_content = match.group(3).strip()

            analyze_resources = options.get('analyze', False)

            # Handle absolute paths and relative paths
            original_kustomize_dir = kustomize_dir

            # Check if this is an auto-discovered path
            if kustomize_dir in self._kustomize_path_mapping:
                kustomize_dir = self._kustomize_path_mapping[kustomize_dir]
            # If it's already an absolute path and exists, use it
            elif os.path.isabs(kustomize_dir) and os.path.isdir(kustomize_dir):
                # Already good to go
                pass
            elif not os.path.isdir(kustomize_dir):
                # Check if it's relative to one of the configured kustomize directories
                found = False
                for base_dir in self.config['kustomize_dirs']:
                    potential_path = os.path.join(base_dir, kustomize_dir)
                    if os.path.isdir(potential_path):
                        kustomize_dir = potential_path
                        found = True
                        break

                if not found:
                    return f"```yaml\n# Error: Kustomize directory '{original_kustomize_dir}' not found\n```"

            try:
                # Run kustomize build on the directory
                result = subprocess.run(
                    ['kustomize', 'build', kustomize_dir],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True,
                    text=True
                )

                output = result.stdout

                # If there's override content, apply it
                if override_content:
                    try:
                        # Parse the kustomize output as YAML
                        kustomize_yaml = list(yaml.safe_load_all(output))

                        # Parse the override content as YAML
                        override_yaml = yaml.safe_load(override_content)

                        if override_yaml and isinstance(override_yaml, dict):
                            # Apply overrides (this is simplistic; in a real implementation
                            # you might want more sophisticated merging)
                            for resource in kustomize_yaml:
                                # Apply only to matching resources if 'kind' and 'metadata.name' match
                                if (override_yaml.get('kind') == resource.get('kind') and
                                    override_yaml.get('metadata', {}).get('name') ==
                                    resource.get('metadata', {}).get('name')):
                                    # Deep merge would be better
                                    resource.update(override_yaml)

                            # Convert back to YAML
                            output = yaml.dump_all(kustomize_yaml, default_flow_style=False)
                    except yaml.YAMLError as e:
                        return f"```yaml\n# Error parsing YAML: {str(e)}\n{override_content}\n```"

                # If analyze flag is set, add resource analysis table
                if analyze_resources:
                    resources_yaml = kustomize_yaml if 'kustomize_yaml' in locals() else list(yaml.safe_load_all(output))
                    resources_table = self.analyze_resources(resources_yaml)
                    return f"## Resources Analysis\n\n{resources_table}"

                return f"```yaml\n{output}\n```"
            except subprocess.SubprocessError as e:
                error_message = e.stderr.decode('utf-8') if hasattr(e, 'stderr') else str(e)
                return f"```yaml\n# Error running kustomize: {error_message}\n```"

        # Replace all kustomize code blocks with their rendered output
        return re.sub(pattern, replace_match, markdown, flags=re.DOTALL)

    def analyze_resources(self, resources):
        """
        Analyze Kubernetes resources and create a table with resource information.
        Each row has expandable YAML content directly underneath it.

        Args:
            resources: List of Kubernetes resource dictionaries

        Returns:
            Markdown table with resource information and expandable details
        """
        if not resources:
            return "No resources found."

        # CSS styling for the collapsible sections
        css_style = """
<style>
.mkdocs-kustomize-plugin .resource-row {
  border-bottom: 1px solid #ddd;
}
.mkdocs-kustomize-plugin .resource-details {
  margin: 0;
  padding: 8px;
  border: 1px solid #ddd;
  border-top: none;
  border-radius: 0 0 4px 4px;
  background-color: #f8f8f8;
}
.mkdocs-kustomize-plugin .resource-details summary {
  cursor: pointer;
  padding: 8px;
  font-weight: bold;
  background-color: #eee;
  border-radius: 4px;
}
.mkdocs-kustomize-plugin .resource-name {
  color: #2196f3;
  word-break: break-word;
}
.mkdocs-kustomize-plugin .resource-api-info {
  color: #777;
  font-size: 0.8em;
  display: block;
  margin-top: 2px;
}
.mkdocs-kustomize-plugin .resource-table {
  border-collapse: collapse;
  width: 100%;
}
.mkdocs-kustomize-plugin .resource-table th {
  background-color: #f2f2f2;
  text-align: left;
  padding: 8px;
}
.mkdocs-kustomize-plugin .resource-table td {
  padding: 8px;
  text-align: left;
  word-wrap: break-word;
  max-width: 250px;
}
</style>
"""
        # Start the HTML table
        result = css_style + "\n<div class='mkdocs-kustomize-plugin resource-analysis'>\n<table class='resource-table'>\n"
        result += "<thead>\n<tr>\n<th>Kind</th>\n<th>Name</th>\n<th>Namespace</th>\n<th>Details</th>\n</tr>\n</thead>\n<tbody>\n"

        resource_index = 1

        for resource in resources:
            if not isinstance(resource, dict):
                continue

            # Extract API group and version
            api_version = resource.get('apiVersion', '')
            if '/' in api_version:
                group, version = api_version.split('/')
            else:
                group = ''
                version = api_version

            kind = resource.get('kind', '')
            name = resource.get('metadata', {}).get('name', '')
            namespace = resource.get('metadata', {}).get('namespace', '')

            # Create the details section ID
            details_id = f"resource-{resource_index}"
            resource_index += 1

            # Create YAML content without displaying namespace redundantly in the header
            yaml_content = yaml.dump(resource, default_flow_style=False)

            # Add a table row with a collapsible section underneath
            api_info = f"{group}/{version}" if group and group.strip() else version
            result += f"""<tr class='resource-row'>
  <td>{kind}<span class="resource-api-info">{api_info}</span></td>
  <td title="{name}">{name}</td>
  <td title="{namespace}">{namespace}</td>
  <td><input type="checkbox" id="{details_id}-check" class="k8s-yaml-checkbox" aria-label="Show YAML for {kind} {name}" /><label for="{details_id}-check" class="k8s-yaml-toggle">▼ YAML</label></td>
</tr>
<tr id="{details_id}-row" class="k8s-yaml-row" data-yaml-id="{details_id}">
  <td colspan="4">
    <div class="resource-details">

```yaml
{yaml_content}
```

    </div>
  </td>
</tr>
"""

        # Close the table and add CSS for toggling (no JavaScript required)
        result += "</tbody>\n</table>\n</div>\n"
        result += """
<style>
/* CSS-only toggle solution that works even when JavaScript is disabled */
.k8s-yaml-checkbox {
  display: none;
}
.k8s-yaml-row {
  display: none;
}
.k8s-yaml-row.k8s-yaml-expanded {
  display: table-row;
}
.k8s-yaml-checkbox:checked + .k8s-yaml-toggle + tr[data-yaml-id] {
  display: table-row;
}
.k8s-yaml-toggle {
  background-color: #f1f8ff;
  border: 1px solid #c5d6e8;
  color: #0366d6;
  padding: 4px 8px;
  border-radius: 3px;
  cursor: pointer;
  user-select: none;
  font-size: 12px;
  display: inline-block;
  text-decoration: none;
}
.k8s-yaml-toggle:hover {
  background-color: #e1f5fe;
  border-color: #0366d6;
}
</style>
<script>
(function() {
  'use strict';

  // Global variables to prevent multiple initializations
  var isSetup = false;
  var observer = null;
  var urlCheckInterval = null;

  function initializeYamlToggles() {
    var toggles = document.querySelectorAll('.k8s-yaml-toggle:not([data-initialized])');
    toggles.forEach(function(toggle) {
      toggle.setAttribute('data-initialized', 'true');
      toggle.addEventListener('click', function(e) {
        e.preventDefault();
        var checkbox = document.getElementById(this.getAttribute('for'));
        var row = document.querySelector('tr[data-yaml-id="' + checkbox.id.replace('-check', '') + '"]');
        if (row) {
          row.classList.toggle('k8s-yaml-expanded');
          // Update button text based on state
          if (row.classList.contains('k8s-yaml-expanded')) {
            this.innerHTML = '▲ YAML';
          } else {
            this.innerHTML = '▼ YAML';
          }
        }
      });
    });
  }

  function setupYamlToggles() {
    if (isSetup) return; // Prevent multiple setups
    isSetup = true;

    // Initialize immediately
    initializeYamlToggles();

    // Set up DOM observer for new content with throttling
    var observerTimeout = null;
    observer = new MutationObserver(function(mutations) {
      if (observerTimeout) return; // Throttle observer

      var shouldReinitialize = false;
      mutations.forEach(function(mutation) {
        if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
          for (var i = 0; i < mutation.addedNodes.length; i++) {
            var node = mutation.addedNodes[i];
            if (node.nodeType === Node.ELEMENT_NODE) {
              if (node.querySelector && node.querySelector('.k8s-yaml-toggle:not([data-initialized])')) {
                shouldReinitialize = true;
                break;
              }
            }
          }
        }
      });

      if (shouldReinitialize) {
        observerTimeout = setTimeout(function() {
          initializeYamlToggles();
          observerTimeout = null;
        }, 100);
      }
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });

    // Listen for MkDocs Material instant navigation if available
    if (typeof app !== 'undefined' && app.location$ && typeof app.location$.subscribe === 'function') {
      app.location$.subscribe(function() {
        setTimeout(initializeYamlToggles, 100);
      });
    }

    // Fallback: Check for URL changes (with cleanup)
    var lastUrl = location.href;
    urlCheckInterval = setInterval(function() {
      if (location.href !== lastUrl) {
        lastUrl = location.href;
        setTimeout(initializeYamlToggles, 100);
      }
    }, 500);
  }

  // Cleanup function for page unload
  function cleanup() {
    if (observer) {
      observer.disconnect();
      observer = null;
    }
    if (urlCheckInterval) {
      clearInterval(urlCheckInterval);
      urlCheckInterval = null;
    }
    isSetup = false;
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupYamlToggles);
  } else {
    setupYamlToggles();
  }

  // Cleanup on page unload
  window.addEventListener('beforeunload', cleanup);
})();
</script>
"""

        return result

    def on_page_context(self, context, page, config, nav):
        """
        Called after the page context is created but before rendering.
        This is where we fix the active state for the Infrastructure section.
        """
        if not self.config['auto_nav_path'] or not self.config['enable_rendering']:
            return context

        # Check if current page is in the kustomize section
        if hasattr(page, 'file') and page.file.src_path.startswith('kustomize/'):
            # Find the Infrastructure section in navigation and mark it as active
            if hasattr(nav, 'items'):
                for nav_item in nav.items:
                    if hasattr(nav_item, 'title') and nav_item.title == self.config['nav_title']:
                        # Mark the section as having an active child
                        if hasattr(nav_item, 'active'):
                            nav_item.active = True
                        # Also check if this page should make the section index active
                        if hasattr(nav_item, 'children'):
                            for child in nav_item.children:
                                if hasattr(child, 'file') and child.file == page.file:
                                    child.active = True
                                    # If this is the index page, also mark parent as directly active
                                    if child.file.src_path == 'kustomize/index.md':
                                        nav_item.active = True
                        break

        return context

    def on_post_build(self, config):
        """
        Called after the build is complete.

        Args:
            config: Global configuration object
        """
        if self.config['enable_rendering']:
            log.info("Kustomize plugin finished processing all pages.")
