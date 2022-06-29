import setuptools

with open('README.md', 'r') as f:
    long_description = f.read()

setuptools.setup(
    name='fontquery',
    description='Query a font in Fedora release',
    long_description_content_type='text/markdown',
    long_description=long_description,
    version='1.0',
    license='MIT',
    author='Akira TAGOH',
    author_email='akira@tagoh.org',
    packages=setuptools.find_packages(),
    package_data = {
        'pyfontquery': ['version.txt'],
    },
    py_modules = [ 'cell_row_span.cell_row_span' ],
    entry_points = {
        'console_scripts': [
            'fontquery-container=pyfontquery.container:main',
            'fontquery=pyfontquery.client:main',
            'fontquery-build=pyfontquery.build:main',
            'fq2html=pyfontquery.htmlformatter:main',
        ],
    },
    url='https://github.com/fedora-i18n/fontquery',
    keywords='fedora fonts',
    install_requires=[
        'markdown',
        'langtable',
    ],
)
