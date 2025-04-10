from setuptools import setup, find_packages

setup(
    name="raiden-plus",
    version="1.0.1",
    packages=find_packages(),
    install_requires=[
        'fastapi',
        'uvicorn[standard]',
        'pywebview',
        'pystray',
        'pillow',
        'keyring',
        'langchain',
        'chromadb',
        # Other dependencies from requirements.txt
    ],
    entry_points={
        'console_scripts': [
            'raiden=desktop:main',
        ],
    },
    include_package_data=True,
    package_data={
        'raiden': ['frontend/*', 'tools/*'],
    },
)
