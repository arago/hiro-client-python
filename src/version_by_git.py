"""
Create/Update a VERSION file in the hiro_graph_client package when setup is triggered.
"""

import os
import re


def create_version_file():
    stream = os.popen('git describe --tags --long --always')
    internal_version = stream.read().strip()

    version_file = open('hiro_graph_client/VERSION', 'w')

    match = re.search('^.([0-9\\.]+)-(.)', internal_version)
    pre_version = match.group(2)
    if int(pre_version) != 0:
        version = "{}-post{}".format(match.group(1), match.group(2))
    else:
        version = match.group(1)

    version_file.write(version)


if __name__ == "__main__":
    create_version_file()
