"""
Create/Update a VERSION file in the package package when setup is triggered.
"""

import logging
import os
import re
import sys

logger = logging.getLogger(__name__)

VERSION_FILENAME = 'VERSION'
FALLBACK_VERSION = '0.0.0.dev0'


def create_version(package: str) -> str:
    """
    Create a python version from a git tag. The git tag has to start with 't' or 'v', followed by at least three
    numbers separated by '.'.

    :param package: Name of the package (usually its subdirectory in *src/*)
    :return: The version string.
    """
    with os.popen('git describe --tags --long --always') as stream:
        internal_version = stream.read().strip()

    regex_pattern = '@?([tv])((?:[0-9]+\\.){2,}[0-9]+)[-_]([0-9]+)'

    match = re.search(regex_pattern, internal_version)
    if not match:
        logger.warning(
            'Git tag "{}" does not match match pattern "{}". Using fallback.'.format(internal_version, regex_pattern))
        return FALLBACK_VERSION

    version_type = match.group(1)
    version_numbers = match.group(2)
    commit_number = match.group(3)

    if version_type == 't':
        version = "{}.dev{}".format(version_numbers, commit_number)
    elif int(commit_number) != 0:
        version = "{}.post{}".format(version_numbers, commit_number)
    else:
        version = version_numbers

    logger.info("Python version %s", version)

    return version


def write_version_file(package: str, version: str):
    """
    Write the version to a file

    :param package: Name of the package (usually its subdirectory in *src/*)
    :param version: Version to write
    """
    with open(os.path.join(package, VERSION_FILENAME), 'w') as version_file:
        version_file.write(version)


def create_version_file(package: str) -> str:
    """
    Create a version file in the *package* and return the version string.

    :param package: Name of the package (usually its subdirectory in *src/*)
    :return: Version string that has been written.
    """
    version = create_version(package)
    write_version_file(package, version)
    return version


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise RuntimeError('Need the name of the python package as parameter.')
    create_version_file(sys.argv[1])
