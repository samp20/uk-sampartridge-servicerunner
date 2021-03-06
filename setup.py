from setuptools import setup, find_namespace_packages

with open('README.md', 'r') as fh:
    long_description = fh.read()

setup(
    name="uk-sampartridge-servicerunner",
    version="0.3.0",
    author="Sam Partridge",
    description="A microservice framework",
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/samp20/uk-sampartridge-servicerunner',
    python_requires='~=3.7',
    packages=find_namespace_packages(),
    entry_points= {
        'console_scripts': ['servicerunner=uk.sampartridge.servicerunner.__main__:main']
    }
)