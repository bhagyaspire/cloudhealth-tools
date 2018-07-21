# CLOUDHEALTH TOOLS

Python3 library and CLI tools to manage CloudHealth. Currently only includes a tool to create and manage CloudHealth perspectives.

## INSTALLATION

Installation for normal everyday usage is done via `pip`.

```
pip3 install chtools
```

For Development a `requirements-dev.txt` file has been provided for installation of necessary Python packages needed for development and testing.

## CONFIGURATION

You will need a CloudHealth API Key to use any of these utilities. You can get your CloudHealth API key by the steps outlined here - https://github.com/CloudHealth/cht_api_guide#getting-an-api-key.

You can set the API Key either via a `CH_API_KEY` environment variable or via a `--api-key` argument.


## TOOLS

### perspective-tool

The tool supports YAML based spec files which can be used to create and update perspectives. Currently only tag based perspectives are supported and not all perspective configurations are supported. Details on the YAML spec files used to create and update perspectives are found later in the README.

List of CLI arguments can be found via the help. Refer to the actual output of help to ensure latest info.
```
usage: perspective-tool [-h] [--api-key API_KEY]
                           [--client-api-id CLIENT_API_ID] [--name NAME]
                           [--spec-file SPEC_FILE] [--log-level LOG_LEVEL]
                           {create,update,delete,get-schema}

Create and manage perspectives via YAML spec files. Tool can also be used to
delete perspective or print a perspective's JSON schema.

positional arguments:
  {create,update,delete,get-schema}
                        Perspective action to take.

optional arguments:
  -h, --help            show this help message and exit
  --api-key API_KEY     CloudHealth API Key. May also be set via the
                        CH_API_KEY environmental variable.
  --client-api-id CLIENT_API_ID
                        CloudHealth client API ID.
  --name NAME           Name of the perspective to get or delete. Name for
                        create or update will come from the spec file
  --spec-file SPEC_FILE
                        Path to the file containing spec for the perspective.
  --log-level LOG_LEVEL
                        Log level sent to the console.

```

**Warning:** Due to a bug in the CloudHealth API groups are unable to be removed from perspectives via the API. Groups that should be deleted via the API will have their associated rules deleted, this will cause them to appear aqua green the Web UI making it easy to identify what should be remove. CleadHealth has acknowledged the bug, but it's unclear when it will be fixed.

#### SPEC FILES
Examples of spec files can be found in `tests/specs`.

Spec files used by `perspective-tool` are in YAML and support the following top-level keys. Required keys are in **bold**.

 * **Name**: Name to set for the perspective.
 * Reports: Boolean if the perspective should be included in the reports. When creating will default to `True`. When updating will default to what is already set for the perspective.
 * **Groups**: A list of group mappings.

Perspective groups are represented via YAML mappings. Each group mapping has the following keys with required keys are in **bold**.

 * **Type**: Group type, with valid values being: `Search`, `Categorize` or `GroupByTagValue`. `Search` and `Categorize` mirror the Web GUI, while `GroupByTagValue` provides a short hand to build multiple groups. Details on `GroupByTagValue` can be found below in the Values key below.
 * Name: Name of the group. This is required for all types except `GroupByTagValue`.
 * **Assets**: A list of CloudHealth Assets to include in the group. Examples include `AwsAsset`, `AwsTaggableAsset` and `AwsEmrCluster`. Note that `Categorize` groups currently only support a single Asset. This is a tool limitation, not a CloudHealth limitation.
 * **Conditions**: A list of mappings defining the conditions in which the type of Assets should be included in the group.

Condition mappings include the following keys:

 * **Type**: Currently `Tag` is the only supported type, causing the condition to match assets with one or more specified tags.
 * **Name**: Name of the tag in which will be matched against.
 * Values: Values is a required key if the group type is `Search` or `GroupByTagValue`. For `Search` Values is either a list of values that should be matched to be included in the group or a boolean, with `True` denoting any Asset with that tag should be included in the group or `False` denoting that any Asset without that tag should not be included. For `GroupByTagValue` Values must be a a list or values that will be used to build perspective groups. With `GroupByTagValue` a separate perspective group will be created for each value included in the list which will include assets matching that list item.

 Note that `Categorize` groups only support a single `Tag` condition. Again this is a limitation of the tool and not CloudHealth.







