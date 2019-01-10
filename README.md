# CLOUDHEALTH TOOLS

Python3 library and CLI tools to manage CloudHealth. Currently only includes a tool to create and manage CloudHealth perspectives. Plans to expand to account and tenant management.

## INSTALLATION

Installation for normal everyday usage is done via `pip`.

```
pip3 install chtools
```

For Development a `requirements-dev.txt` file has been provided for installation of necessary Python packages needed for development and testing.

## CONFIGURATION

You will need a CloudHealth API Key to use any of these utilities. You can get your CloudHealth API key by the steps outlined here - https://github.com/CloudHealth/cht_api_guide#getting-an-api-key.

You can set the API Key either via a `CH_API_KEY` environment variable or via a `--api-key` argument.

As a provider you can specify a `--client-api-id` argument to perform actions against a tenant.


## TOOLS

These tools are installed into your path to be used via the CLI.

### perspective-tool

The perspective-tool provides a programmatic way to interact with perspectives. It can do this either via [raw JSON schemas as described in the CloudHealth API Guide](http://apidocs.cloudhealthtech.com/#perspectives_introduction-to-perspectives-api) or via YAML based spec files.

The YAML based spec files are based on the JSON schema, but some "syntactical sugar" has been implemented to make them a bit more human friendly. YAML spec files support the following features:

* In the schema a rule can either ba a `filter` rule or a `categorize` rule. In the Web UI the `filter` rules are refereed to as `search` rules. Spec files allow you to use `filter` and `search` interchangeably.
* You don't need to worry about ref_ids or constructing Dynamic Groupings. You can reference the name of a perspective group you'd like the rule to use instead of needing the ref_id. `perspective-tool` will retrieve the correct ref_id based on the name or generate a new one if it's a new perspective group. This means new perspective groups are created just by referring to them.
* In the schema, `filter` rules use the `to` key to determine the perspective group it references, while `categorize` uses `ref_id`. Spec files allow you to use `to` for `categorize` as well, this makes things a bit more consistent between the two rule types. *Note: `categorize` rules currently have both a `to` and `name` keys, but spec will likely drop the need to specify the `name` key in the future.*
* The schema has many keys that require only a single item list as a value. Spec files support these as just string values.
* Spec files support lists of asset types for `filter` rules. A rule in the schema can only apply to a single asset type. This can lead to many rules that do almost the exact same thing. For example to get all taggable financial assets into a perspective group you need to includes rules for the assets: `AwsAsset`, `AwsTaggableAsset` & `AwsEmrCluster` *(it's possible the last one `AwsEmrCluster` is no longer needed)*. If you had three tags you wanted use to put into a single perspective group, then you would need 9 rules, 1 per tag per asset type. This features does need to be used with caution as some asset types don't really make sense with certain condition clauses. Recommended to just stick to combining asset types that utilize `tag_field`. Asset types included in a list like this should be considered logical ORs.


List of CLI arguments can be found via the help. Refer to the actual output of help to ensure latest info.
```
usage: perspective-tool [-h] [--api-key API_KEY]
                        [--client-api-id CLIENT_API_ID] [--name NAME]
                        [--spec-file SPEC_FILE] [--schema-file SCHEMA_FILE]
                        [--log-level LOG_LEVEL]
                        {create,delete,empty-archive,get-schema,get-spec,list,update}

Create and manage perspectives from the command line.

positional arguments:
  {create,delete,empty-archive,get-schema,get-spec,list,update}
                        Perspective action to take.

optional arguments:
  -h, --help            show this help message and exit
  --api-key API_KEY     CloudHealth API Key. May also be set via the
                        CH_API_KEY environmental variable.
  --client-api-id CLIENT_API_ID
                        CloudHealth client API ID.
  --name NAME           Name of the perspective to get or delete. Name for
                        create or update will come from the spec or schema
                        file.
  --spec-file SPEC_FILE
                        Path to the file containing YAML spec used to create
                        or update the perspective.
  --schema-file SCHEMA_FILE
                        Path to the file containing JSON schema used to create
                        or update the perspective.
  --log-level LOG_LEVEL
                        Log level sent to the console.


```

**Warning:** Due to a bug in the CloudHealth API groups are unable to be removed from perspectives via the API. Groups that should be deleted via the API will have their associated rules deleted, this will cause them to appear aqua green the Web UI making it easy to identify what should be remove. CleadHealth has acknowledged the bug, but it's unclear when it will be fixed.

#### SPEC FILES
Being familiar with [CloudHealth Perspective Schemas](http://apidocs.cloudhealthtech.com/#perspectives_introduction-to-perspectives-api) will help when dealing with spec files.

Examples of spec files can be found in `tests/specs`.

It's also a good idea create a rule in the Web GUI and then use the `perspective-tool` to look at the YAML spec for that perspective. Getting the YAML spec for a perspective can be done using a command such as:

```
perspective-tool get-spec --name test-perspective
```

Spec files used by `perspective-tool` are in YAML and support the following top-level keys, which all are required. Note all keys are lower case.

 * name: Name of the perspective.
 * include_in_reports: string 'true' or 'false'.
 * match_lowercase_tag_field: boolean. If true, then filter rules will always match the lowercase value of the tag_field in the filter rule clauses. For example if the rule matches the tag name of "Test" then a clause will be added to match the tag name of "test" as well.
 * match_lowercase_tag_val: boolean. Same as match_lowercase_tag_field but for the values of the tag instead of the tag name.

 * rules: A list of rule mappings.

Each rule is a YAML mapping, with two types of rules `filter` and `categorize`.

`filter` rules have the following keys:

 * type: either `filter` or `search`
 * asset: either a string of a valid asset type or a list of valid asset types. Again some asset types may not make sense together in the same rule.
 * to: The name of the perspective group that resources matching this rule should be assigned to. New groups will be created as needed.
 * condition: A YAML mapping with the following keys:
   * clauses: a list of clauses. It's really best to just go look at examples in `tests/specs` for what clauses look look. There can be nuances from one clause type to another, so best to create the rule in web GUI and then export the spec and see how it's been generated.
   * combine_with: required and only allowed if the list of clauses include more than one item. Set to either OR or AND (uppercase) based on how you want the clauses evaluated.

`categorize` rules have the following keys for categorizing by tag. If you want to categorize by something else, then create the rule in web GUI and then export the spec and see how it's been generated.
 * type: `categorize`
 * asset: a string of a valid asset type (list not supported here for now, not sure API will support).
 * to: The name of the perspective group resources matching this rule should be assigned to. New groups will be created as needed. Should be the set to be the same as `name`.
 * name: This is the name that will of the perspective group that will be  displayed. Should be the set to be the same as `to`.
 * tag_field: The name of the tag to categorize by.

#### Caveats
The goal is for this tool to be somewhat generic, but it has really only been tested for certain use cases specific to deal with AWS resources.
