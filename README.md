# CloudHealth Client

This repo contains a python based CloudHealth client along with utilities and scripts to automate tasks within CloudHealth.

Currently just covers perspectives, but will grow as needed to manage other parts of CloudHealth.

**simple-perspective.py**

Utility to create, update and delete perspectives. Only supports creating and updating "simple perspectives". In this case a simple perspective is where all groups are based off a single tag value.

In addition to groups based off a tag value a "catch all" group can be created which will include any resource that has the tag, but not a value that maps to another group. This allows for separating resources that are tagged (possibly incorrectly) vs resources that are not tagged.