from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="django-jobs",
    version="0.1.0",
    author="Berjan",
    author_email="berjan@bruens.it",
    description="A Django app for managing scheduled management commands",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/berjan/django-jobs",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Framework :: Django",
        "Framework :: Django :: 3.2",
        "Framework :: Django :: 4.0",
        "Framework :: Django :: 4.1",
        "Framework :: Django :: 4.2",
    ],
    python_requires=">=3.8",
    install_requires=[
        "Django>=3.2",
    ],
    include_package_data=True,
    package_data={
        'django_jobs': [
            'templates/admin/*.html',
            'migrations/*.py',
        ],
    },
)