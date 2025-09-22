from setuptools import setup, find_packages

setup(
    name='mkdocs-kustomize',
    version='1.0.0',
    description='A MkDocs plugin for Kustomize integration with auto-discovery and resource analysis',
    author='Your Name',
    author_email='your.email@example.com',
    url='https://github.com/yourusername/mkdocs-kustomize',
    packages=find_packages(),
    install_requires=[
        'mkdocs>=1.1.0',
        'pyyaml>=5.1'
    ],
    entry_points={
        'mkdocs.plugins': [
            'kustomize = mkdocs_kustomize.plugin:KustomizePlugin',
        ]
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Topic :: Documentation',
        'Topic :: Software Development :: Documentation',
    ],
    python_requires='>=3.6',
)
