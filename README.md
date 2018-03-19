# CLOUDHEALTH CLIENT

This repo contains a python based CloudHealth client along with utilities and scripts to automate tasks within CloudHealth.

Currently just covers perspectives, but will grow as needed to manage other parts of CloudHealth.

## INSTALLATION

client and utilities are written in Python3.

A requirements.txt file has been provided for installation of necessary Python packages.

## UTILITIES

You will need a CloudHealth API Key to use any of these utilities. You can get your CloudHealth API key by the steps outlined here - https://github.com/CloudHealth/cht_api_guide#getting-an-api-key.

You can set the API Key either via a `CH_API_KEY` environment variable or via a `--ApiKey` argument.

### perspective.py

Utility to create, update and delete perspectives. Currently only supports creating and updating "simple perspectives". In this case a simple perspective is where all groups are based off a the same tag value.

Groups are created based off a list of values stored in a text file. One group name per line. Group names are case sensitive.

In addition to groups based off a tag value, a "catch all" group can be created which will include any resource that has the tag, but not a value that maps to another group. This allows for separating resources that are tagged (possibly incorrectly) vs resources that are not tagged (which will show up as "Not Allocated" in reports".

```
usage: perspective.py [-h] [--ApiKey APIKEY] [--ClientApiId CLIENTAPIID]
                      --Name NAME [--Tag TAG] [--GroupsFile GROUPSFILE]
                      [--CatchAllName CATCHALLNAME] [--LogLevel LOGLEVEL]
                      {create-simple,update-simple,delete}
```

By default the name of the tag used to drive the perspective will match the name of the perspective. This can be overridden with the `--Tag` argument.

Create a new perspective based of the tag "Environment" using a list of group names found in the file environments.txt. Also adds a catch all group called "Non-Conforming"

```
./perspective.py create-simple --Name Environment --GroupsFile environments.txt --CatchAllName "Non-Conforming"
```

Updating this perspective with an updated list of groups.

```
./perspective.py update-simple --Name Environment --GroupsFile updated-environments.txt --CatchAllName "Non-Conforming"
```

Note you need to specify `--CatchAllName` with the update command for it to continue to be a perspective group. Conversely you can remove the catch all group by omitting the `--CatchAllName` argument.

**Warning:** Due to a bug in the CloudHealth API groups are unable to be removed from perspectives via the API. In the example above any groups not included in the updated-environments.txt file should be deleted, but this is currently not the case. In this case any groups you wish to remove must be deleted via the Web UI. Groups that should be deleted via the API will have their associated rules deleted, this will cause them to appear aqua green the Web UI making it easy to identify what should be remove. This bug is expected to be fixed in early April 2018.