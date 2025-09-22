import os
import unittest
import unittest.mock
import subprocess
from unittest.mock import patch, MagicMock
import tempfile
import yaml
from mkdocs_kustomize.plugin import KustomizePlugin

class TestKustomizePlugin(unittest.TestCase):

    def setUp(self):
        self.plugin = KustomizePlugin()
        # Default config for testing
        self.plugin.config = {
            'kustomize_path': 'kustomize',
            'kustomize_dirs': [],
            'enable_rendering': True
        }

    @patch('subprocess.run')
    def test_on_config(self, mock_run):
        # Mock the subprocess.run to simulate kustomize availability
        mock_run.return_value = MagicMock()

        config = {}
        result = self.plugin.on_config(config)

        # Check that kustomize was verified
        mock_run.assert_called_once_with(
            ['oc', 'version'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )

        # Config should be returned unchanged
        self.assertEqual(result, config)

    @patch('subprocess.run')
    def test_on_page_markdown_basic(self, mock_run):
        # Mock successful kustomize build
        mock_process = MagicMock()
        mock_process.stdout = "apiVersion: v1\nkind: ConfigMap\nmetadata:\n  name: test-configmap"
        mock_run.return_value = mock_process

        markdown = "# Test Page\n\n```kustomize /path/to/kustomize\n```\n\nMore content"

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a mock directory structure
            os.makedirs(os.path.join(temp_dir, 'path', 'to', 'kustomize'))

            # Patch isdir to return True for our test path
            with patch('os.path.isdir', return_value=True):
                result = self.plugin.on_page_markdown(markdown, {}, {}, {})

                # Check that the kustomize code block was replaced with yaml block
                self.assertIn("```yaml", result)
                self.assertIn("kind: ConfigMap", result)

    @patch('subprocess.run')
    def test_on_page_markdown_with_override(self, mock_run):
        # Mock kustomize build output
        kustomize_output = """
apiVersion: v1
kind: ConfigMap
metadata:
  name: test-configmap
data:
  key1: value1
  key2: value2
"""
        mock_process = MagicMock()
        mock_process.stdout = kustomize_output
        mock_run.return_value = mock_process

        # Markdown with override
        markdown = """# Test Page

```kustomize /path/to/kustomize
kind: ConfigMap
metadata:
  name: test-configmap
data:
  key1: new-value
  key2: value2
```

More content"""

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a mock directory structure
            os.makedirs(os.path.join(temp_dir, 'path', 'to', 'kustomize'))

            # Patch isdir to return True for our test path
            with patch('os.path.isdir', return_value=True):
                result = self.plugin.on_page_markdown(markdown, {}, {}, {})

                # The result should contain the updated YAML
                self.assertIn("key1: new-value", result)
                self.assertIn("key2: value2", result)

    def test_disabled_plugin(self):
        # Test when plugin is disabled
        self.plugin.config['enable_rendering'] = False

        markdown = "# Test Page\n\n```kustomize /path/to/kustomize\n```\n\nMore content"
        result = self.plugin.on_page_markdown(markdown, {}, {}, {})

        # Markdown should be unchanged when plugin is disabled
        self.assertEqual(result, markdown)

    @patch('subprocess.run')
    def test_kustomize_error(self, mock_run):
        # Mock kustomize failure
        error = subprocess.SubprocessError()
        error.stderr = b"Kustomize error"
        mock_run.side_effect = error

        markdown = "# Test Page\n\n```kustomize /path/to/kustomize\n\n```\n\nMore content"

        with patch('os.path.isdir', return_value=True):
            result = self.plugin.on_page_markdown(markdown, {}, {}, {})

            # Should contain error message
            self.assertIn("Error", result)

    @patch('subprocess.run')
    def test_on_page_markdown_with_analyze(self, mock_run):
        # Mock kustomize build output
        kustomize_output = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-deployment
  namespace: test-ns
spec:
  replicas: 3
---
apiVersion: v1
kind: Service
metadata:
  name: test-service
spec:
  ports:
  - port: 80
"""
        mock_process = MagicMock()
        mock_process.stdout = kustomize_output
        mock_run.return_value = mock_process

        # Markdown with analyze option
        markdown = """# Test Page

```kustomize /path/to/kustomize [analyze=true]

```

More content"""

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a mock directory structure
            os.makedirs(os.path.join(temp_dir, 'path', 'to', 'kustomize'))

            # Patch isdir to return True for our test path
            with patch('os.path.isdir', return_value=True):
                result = self.plugin.on_page_markdown(markdown, {}, {}, {})

                # Check that the kustomize code block was replaced with a resource table
                self.assertIn("## Resources Analysis", result)
                self.assertIn("<table class='resource-table'>", result)
                self.assertIn("<th>Kind</th>", result)
                self.assertIn("<th>Name</th>", result)
                self.assertIn("<th>Namespace</th>", result)
                self.assertIn("<th>Details</th>", result)
                self.assertIn("<span class=\"resource-api-info\">apps/v1</span>", result)
                self.assertIn("<td>Deployment", result)
                self.assertIn("<td title=\"test-deployment\">test-deployment</td>", result)
                self.assertIn("<td title=\"test-ns\">test-ns</td>", result)
                self.assertIn("<td title=\"\"></td>", result)
                self.assertIn("▼ YAML", result)
                self.assertIn("k8s-yaml-row", result)
                self.assertIn("k8s-yaml-toggle", result)
                self.assertIn("k8s-yaml-checkbox", result)
                self.assertIn("data-yaml-id", result)
                self.assertNotIn("<span class='resource-kind'>", result)
                self.assertNotIn("<span class='resource-name'>", result)
                self.assertIn("```yaml", result)

    def test_analyze_resources(self):
        # Test the resource analysis function directly
        resources = [
            {
                'apiVersion': 'apps/v1',
                'kind': 'Deployment',
                'metadata': {
                    'name': 'test-deployment',
                    'namespace': 'test-ns'
                }
            },
            {
                'apiVersion': 'v1',
                'kind': 'Service',
                'metadata': {
                    'name': 'test-service'
                }
            },
            {
                'apiVersion': 'v1',
                'kind': 'Namespace',
                'metadata': {
                    'name': 'test-namespace'
                }
            }
        ]

        table = self.plugin.analyze_resources(resources)

        # Verify table content
        self.assertIn("<div class='mkdocs-kustomize-plugin resource-analysis'>", table)
        self.assertIn("<table class='resource-table'>", table)
        self.assertIn("<th>Kind</th>", table)
        self.assertIn("<span class=\"resource-api-info\">apps/v1</span>", table)
        self.assertIn("<td>Deployment", table)
        self.assertIn("<td title=\"test-deployment\">test-deployment</td>", table)
        self.assertIn("<td title=\"test-ns\">test-ns</td>", table)
        self.assertIn("<td title=\"test-service\">test-service</td>", table)
        self.assertIn("<td title=\"\"></td>", table)
        self.assertIn("▼ YAML", table)
        self.assertIn("k8s-yaml-toggle", table)
        self.assertIn("k8s-yaml-checkbox", table)
        self.assertIn("data-yaml-id", table)
        self.assertNotIn("<span class='resource-kind'>", table)
        self.assertNotIn("<span class='resource-name'>", table)
        self.assertIn("```yaml", table)
        self.assertIn("<style>", table)
        self.assertIn(".k8s-yaml-row {", table)

    @patch('os.walk')
    @patch('os.path.exists')
    @patch('os.path.isabs')
    def test_find_kustomize_directories(self, mock_isabs, mock_exists, mock_walk):
        # Mock directory structure with kustomization files
        mock_walk.return_value = [
            ('/base/path/app1', [], ['kustomization.yaml', 'deployment.yaml']),
            ('/base/path/app2', [], ['kustomization.yml', 'service.yaml']),
            ('/base/path/app3', [], ['deployment.yaml']),  # No kustomization file
        ]
        mock_exists.return_value = True
        mock_isabs.return_value = True

        result = self.plugin._find_kustomize_directories('/base/path')

        self.assertEqual(len(result), 2)
        self.assertIn('/base/path/app1', result)
        self.assertIn('/base/path/app2', result)
        self.assertNotIn('/base/path/app3', result)

    @patch('os.walk')
    @patch('os.path.exists')
    @patch('os.path.isabs')
    def test_find_nested_kustomize_directories(self, mock_isabs, mock_exists, mock_walk):
        # Mock nested directory structure with kustomization files
        mock_walk.return_value = [
            ('/base/path', ['overlays', 'base'], []),
            ('/base/path/base', [], ['kustomization.yaml', 'deployment.yaml']),
            ('/base/path/overlays', ['dev', 'prod'], []),
            ('/base/path/overlays/dev', [], ['kustomization.yaml', 'patch.yaml']),
            ('/base/path/overlays/prod', [], ['kustomization.yml', 'patch.yaml']),
            ('/base/path/overlays/staging', [], ['deployment.yaml']),  # No kustomization file
        ]
        mock_exists.return_value = True
        mock_isabs.return_value = True

        result = self.plugin._find_kustomize_directories('/base/path')

        self.assertEqual(len(result), 3)
        self.assertIn('/base/path/base', result)
        self.assertIn('/base/path/overlays/dev', result)
        self.assertIn('/base/path/overlays/prod', result)
        self.assertNotIn('/base/path/overlays/staging', result)

    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data="# App README\n\nThis is a test application.")
    @patch('os.path.exists')
    def test_generate_kustomize_page_content(self, mock_exists, mock_open):
        mock_exists.return_value = True

        content = self.plugin._generate_kustomize_page_content('/path/to/test-app', 'test-app')

        self.assertIn('# Test App', content)
        self.assertIn('This is a test application.', content)
        self.assertIn('## Kustomize Configuration', content)
        self.assertIn('```kustomize test-app [analyze=true]', content)

    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data="Regular content without title")
    @patch('os.path.exists')
    def test_generate_kustomize_page_content_no_title(self, mock_exists, mock_open):
        mock_exists.return_value = True

        content = self.plugin._generate_kustomize_page_content('/path/to/my-service', 'my-service')

        self.assertIn('# My Service', content)
        self.assertIn('Regular content without title', content)
        self.assertIn('```kustomize my-service [analyze=true]', content)

    @patch('os.path.exists')
    def test_generate_kustomize_page_content_no_readme(self, mock_exists):
        mock_exists.return_value = False

        content = self.plugin._generate_kustomize_page_content('/path/to/app', 'app')

        self.assertIn('# App', content)
        self.assertIn('## Kustomize Configuration', content)
        self.assertIn('```kustomize app [analyze=true]', content)
        self.assertNotIn('README', content)

if __name__ == '__main__':
    unittest.main()
