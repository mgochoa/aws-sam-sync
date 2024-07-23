from setuptools import setup

setup(
    name='aws_sam_sync',
    version='0.1.0',
    py_modules=['aws_sam_sync'],
    install_requires=[
        'Click',
        'GitPython',
        'boto3'
    ],
    entry_points={
        'console_scripts': [
            'aws-sam-sync = aws_sam_sync:cli',
        ],
    },
)