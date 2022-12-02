from setuptools import find_packages, setup

setup(
    name='ai_blog',
    version='0.8.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'flask',
    ],
)