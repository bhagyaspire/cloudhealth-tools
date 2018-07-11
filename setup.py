from setuptools import setup

with open('README.md') as readme_file:
      readme =  readme_file.read()

setup(name='cloudhealth-perspective_tool',
      version='0.1',
      description='Tool to create and manage CloudHealth perspectives',
      url='https://github.com/bluechiptek/cloudhealth-perspective-tool',
      author='BlueChipTek',
      author_email='joe@bluechiptek.com',
      long_description_content_type='text/markdown',
      long_description=readme,
      license='GPLv3',
      packages=['cloudhealth_perspective_tool'],
      install_requires=[
            'certifi==2018.1.18',
            'chardet==3.0.4',
            'idna==2.6',
            'PyYAML==3.13',
            'requests==2.18.4',
            'urllib3==1.22'
      ],
      classifiers=[
            'License :: OSI Approved :: GNU General Public License v3 (GPLv3)'
      ]
      )
