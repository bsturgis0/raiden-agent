from setuptools import setup, find_packages

# Read requirements
with open('requirements.txt') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="raiden-plus",
    version="1.0.1",
    author="Raiden Team",
    description="Raiden+ AI Desktop Assistant",
    long_description=open('DESKTOP_README.md').read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'raiden=desktop:main',
        ],
    },
    include_package_data=True,
    package_data={
        'raiden': [
            'frontend/*',
            'frontend/assets/*',
            'frontend/assets/icons/*',
            'tools/*',
        ],
    },
    python_requires='>=3.9',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Desktop Environment :: AI Assistant',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Operating System :: OS Independent',
        'Environment :: Desktop',
    ],
    keywords='ai assistant, desktop, nlp, chat',
)
