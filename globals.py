from pathlib import Path as _Path

SETUP_DIRS = (
    'build',
    'chained.egg-info',
    'dist'
)
MYPY_CACHE_DIR = '.mypy_cache'

VERSION = '0.0.5'
SLOGAN = 'Making Python language more functional'
PROJECT_NAME = 'chained'
PROJECT_URL = 'https://github.com/andrewsonin/chained'

PROJECT_DIR = _Path(__file__).parent
README_FILE = PROJECT_DIR / 'README.md'

CONDA_YML_FILE = 'meta.yaml'
CONDA_SH_FILE = 'build.sh'
CONDA_BAT_FILE = 'bld.bat'

PYTHON_VERSION = '~=3.8'
LICENCE = 'MIT License'

AUTHOR = 'Andrew Sonin'
EMAIL = 'sonin.cel@gmail.com'

PYPI_USERNAME = 'andrewsonin'
PYPI_PWSD_FILE = 'PYPI_PSWD'
PYPI_UPLOAD_FILE = 'upload.sh'
