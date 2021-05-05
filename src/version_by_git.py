"""
Create/Update a VERSION file in the package package when setup is triggered.
"""

import os
import re
import sys


def create_version_file(package: str):
    stream = os.popen('git describe --tags --long --always')
    internal_version = stream.read().strip()

    version_file = open(package + '/VERSION', 'w')

    regex_pattern = '@?([tv])([0-9.]+)-(.)'

    match = re.search(regex_pattern, internal_version)
    if not match:
        raise RuntimeError('Git tag "{}" needs to match pattern "{}".'.format(internal_version, regex_pattern))

    version_type = match.group(1)
    commit_number = match.group(3)

    if version_type == 't':
        version = "{}.dev{}".format(match.group(2), match.group(3))
    elif int(commit_number) != 0:
        version = "{}.post{}".format(match.group(2), match.group(3))
    else:
        version = match.group(1)

    version_file.write(version)


if __name__ == "__main__":
    create_version_file(sys.argv[1])
