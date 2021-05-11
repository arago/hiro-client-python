"""
Create/Update a VERSION file in the package package when setup is triggered.
"""

import os
import re
import sys

VERSION_FILENAME = 'VERSION'


def create_version_file(package: str):
    """
    Create a python version from a git tag. The git tag has to start with 't' or 'v', followed by at least three
    numbers separated by '.'.

    :param package: Name of the package (usually its subdirectory in *src/*)
    """
    with os.popen('git describe --tags --long --always') as stream:
        internal_version = stream.read().strip()

    regex_pattern = '@?([tv])((?:[0-9]+\\.){2,}[0-9]+)-(.)'

    match = re.search(regex_pattern, internal_version)
    if not match:
        raise RuntimeError('Git tag "{}" needs to match pattern "{}".'.format(internal_version, regex_pattern))

    version_type = match.group(1)
    version_numbers = match.group(2)
    commit_number = match.group(3)

    if version_type == 't':
        version = "{}.dev{}".format(version_numbers, commit_number)
    elif int(commit_number) != 0:
        version = "{}.post{}".format(version_numbers, commit_number)
    else:
        version = version_numbers

    with open(os.path.join(package, VERSION_FILENAME), 'w') as version_file:
        version_file.write(version)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise RuntimeError('Need the name of the python package as parameter.')
    create_version_file(sys.argv[1])
