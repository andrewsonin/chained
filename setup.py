from pathlib import Path
from typing import Final

from setuptools import setup, find_packages  # type: ignore

project_dir: Final = Path(__file__).parent

with open(project_dir / 'README.md', 'r') as readme:
    long_desc: Final = readme.read()

setup(
    name='chained',
    version='0.0.2',
    url='https://github.com/andrewsonin/chained',
    license='MIT',
    author='Andrew Sonin',
    author_email='sonin.cel@gmail.com',
    description='Making Python language more functional',
    packages=find_packages(
        exclude=['test']
    ),
    classifiers=[
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries',
        'Operating System :: OS Independent',
        'Typing :: Typed',
        'Development Status :: 2 - Pre-Alpha',
        'License :: OSI Approved :: MIT License',
    ],
    long_description=long_desc,
    long_description_content_type='text/markdown',
    zip_safe=True,
    python_requires='~=3.8'
)
