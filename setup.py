from setuptools import setup, find_packages

with open('README.md') as readme_file:
      readme = readme_file.read()

setup(name='chtools',
      version='1.0.2',
      description='Automation Tools for CloudHealth',
      url='https://github.com/bluechiptek/cloudhealth-tools',
      author='BlueChipTek',
      author_email='joe@bluechiptek.com',
      long_description_content_type='text/markdown',
      long_description=readme,
      license='GPLv3',
      packages=find_packages(),
      install_requires=[
            'certifi==2018.1.18',
            'chardet==3.0.4',
            'idna==2.6',
            'PyYAML==3.13',
            'requests==2.18.4',
            'urllib3==1.22'
      ],
      entry_points={
            'console_scripts': ['perspective-tool=chtools.perspective_tool:main']
      },
      classifiers=[
            'License :: OSI Approved :: GNU General Public License v3 (GPLv3)'
      ]
      )
