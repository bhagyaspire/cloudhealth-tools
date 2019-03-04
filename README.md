# CLOUDHEALTH TOOLS

Python3 library and CLI tool to manage CloudHealth.

## INSTALLATION

Installation for normal everyday usage is done via `pip`.

```
pip3 install chtools
```

For development and testing a `requirements-dev.txt` file has been provided for installation of necessary Python packages.

## CONFIGURATION

You will need a CloudHealth API Key to use any of these utilities. You can get your CloudHealth API key by the steps outlined here - https://github.com/CloudHealth/cht_api_guide#getting-an-api-key.

You can set the API Key either via a `CH_API_KEY` environment variable or via a `--api-key` argument.

As a provider you can specify a `--client-api-id` argument to perform actions against a tenant.


## CLI TOOL USAGE

A `chtools` CLI utility is the main way the CloudHealth tools are intended to be used. The `chtools` has several "subcommands" to indicated what feature of CloudHealth you would like to interact with. Each feature has several "subcommands" to indication what action you wish to take. In general it's:

```
$ chtools featrue command --arg-name arg-value
```

Specific examples looks like this

```
$ chtools aws-account create --name new-account --assume-role-arn arn:aws:iam::123456789012:role/CloudHealth
$ chtools perspective get-schema --name my-perspective
```

You can specify `help` for the feature or command to get context specific help.

### GLOBAL ARGS
Info on args that apply to all features and commands can be viewed via help. Refer to the actual output of help to ensure latest info.

```
usage: chtools [--api-key API_KEY] [--client-api-id CLIENT_API_ID]
               [--log-level LOG_LEVEL]
               {aws-account,perspective,help}

CLI to interact with CloudHealth.

positional arguments:
  {aws-account,perspective,help}
                        CloudHealth feature that you wish to interact with.

optional arguments:
  --api-key API_KEY     CloudHealth API Key. May also be set via the
                        CH_API_KEY environmental variable.
  --client-api-id CLIENT_API_ID
                        CloudHealth client API ID.
  --log-level LOG_LEVEL
                        Log level sent to the console.
```

### aws-account
The `aws-account` feature is used to create and manage AWS accounts. Info on the args that can be used when using the `aws-account` feature can be viewed via help. Refer to the actual output of help to ensure latest info.

```
usage: chtools aws-account [--account-id ACCOUNT_ID]
                           [--assume-role-arn ASSUME_ROLE_ARN]
                           [--dbr-bucket DBR_BUCKET] [--name NAME]
                           [--owner-id OWNER_ID] [--spec-file SPEC_FILE]
                           [--schema-file SCHEMA_FILE]
                           {create,delete,get-schema,get-spec,help,list,update}

Create and manage AWS Accounts

positional arguments:
  {create,delete,get-schema,get-spec,help,list,update}
                        Account action to take.

optional arguments:
  --account-id ACCOUNT_ID
                        CloudHealth Account Id for the AWS Account to interact
                        with. Can not specify with --name or --owner-id.
  --assume-role-arn ASSUME_ROLE_ARN
                        The ARN of the role that account should use to connect
                        to the AWS Account
  --dbr-bucket DBR_BUCKET
                        The name of the bucket used to store the DBR reports.
  --name NAME           Name of the AWS Account to interact with. Can not
                        specify with --account-id or --owner-id when getting
                        schema or spec. Specifying name with create or update
                        with change the accounts name.
  --owner-id OWNER_ID   AWS Account Id for the AWS Account to interact with.
                        Can not specify with --name or --account-id.
  --spec-file SPEC_FILE
                        Path to the YAML spec file to create or update an AWS
                        Account.
  --schema-file SCHEMA_FILE
                        Path to the JSON spec file to create or update an AWS
                        Account.
```


Creating or deleting account is only in the context of CloudHealth's connection to the AWS account. CLI Args can be use to supply most common config options needed to connect to an account.

```
$ chtools aws-account create --name my-account --assume-role-arn arn:aws:iam::123456789012:role/CloudHealth --dbr-bucket org-ch-dbr-bucket
```
If you wish to supply more config options, say for example configure CloudTrail bucket, then you will need to use a JSON schema or YAML spec file (spec file is just the JSON Schema in YAML format). You can specify the schema or spec file as the input to the command. See the CloudHealth API docs and contents of `tests/account_data` for more details on the AWS Account schema.

A few notes:
* Currently the CUR bucket can not be set via API :-(
* `account-id` refers the id number of the AWS Account in CloudHealth. This is different than the AWS Account id for the account, which is refereed to as `owner-id`.


### perspective
The `perspective` feature is used to create and manage CloudHealth perspectives. Interaction with perspectives is done either via [raw JSON schemas as described in the CloudHealth API Guide](http://apidocs.cloudhealthtech.com/#perspectives_introduction-to-perspectives-api) or via YAML based spec files.

The YAML based spec files are based on the JSON schema, but some "syntactical sugar" has been implemented to make them a bit more human friendly. YAML spec files support the following features:

* In the schema a rule can either ba a `filter` rule or a `categorize` rule. In the Web UI the `filter` rules are refereed to as `search` rules. Spec files allow you to use `filter` and `search` interchangeably.
* You don't need to worry about ref_ids or constructing Dynamic Groupings. You can reference the name of a perspective group you'd like the rule to use instead of needing the ref_id. `chtools perspective` will retrieve the correct ref_id based on the name or generate a new one if it's a new perspective group. This means new perspective groups are created just by referring to them.
* In the schema, `filter` rules use the `to` key to determine the perspective group it references, while `categorize` uses `ref_id`. Spec files allow you to use `to` for `categorize` as well, this makes things a bit more consistent between the two rule types. *Note: `categorize` rules currently have both a `to` and `name` keys, but spec will may drop the need to specify the `name` key in the future.*
* The schema has many keys that require only a single item list as a value. Spec files support these as just string values.
* Spec files support lists of asset types for `filter` rules. A rule in the schema can only apply to a single asset type. This can lead to many rules that do almost the exact same thing. For example to get all taggable financial assets into a perspective group you need to includes rules for the assets: `AwsAsset`, `AwsTaggableAsset` & `AwsEmrCluster` *(it's possible the last one `AwsEmrCluster` is no longer needed)*. If you had three tags you wanted use to put into a single perspective group, then you would need 9 rules, 1 per tag per asset type. This features does need to be used with caution as some asset types don't really make sense with certain condition clauses. Recommended to just stick to combining asset types that utilize `tag_field`. Asset types included in a list like this should be considered logical ORs.

Info on the args that can be used when using the `perspective` feature can be viewed via help. Refer to the actual output of help to ensure latest info.

```
usage: chtools perspective [--name NAME] [--spec-file SPEC_FILE]
                           [--schema-file SCHEMA_FILE]
                           {create,delete,empty-archive,get-schema,get-spec,help,list,update}

Create and manage perspectives

positional arguments:
  {create,delete,empty-archive,get-schema,get-spec,help,list,update}
                        Perspective action to take.

optional arguments:
  --name NAME           Name of the perspective to get or delete. Name for
                        create or update will come from the spec or schema
                        file.
  --spec-file SPEC_FILE
                        Path to the file containing YAML spec used to create
                        or update the perspective.
  --schema-file SCHEMA_FILE
                        Path to the file containing JSON schema used to create
                        or update the perspective.
```

*Note*: Initally `chtools perspective` was released as a stand alone CLI utility called `perspective-tool`. `chtools perspective` is functionally equivalent to `perspective-tool` (same code, just different CLI wrapper). `perspective-tool` is still available, but should be considered depreciated.

#### SPEC FILES
Being familiar with [CloudHealth Perspective Schemas](http://apidocs.cloudhealthtech.com/#perspectives_introduction-to-perspectives-api) will help when dealing with spec files.

Examples of spec files can be found in `tests/perspective_data/specs`.

It's also a good idea to create a rule in the Web GUI and then use the `chtools perspective get-spec --name perspective-name` to look at the YAML spec for that perspective.

Spec files used by `chtools perspective` are in YAML and support the following top-level keys, which all are required. Note all keys are lower case.

 * name: Name of the perspective.
 * include_in_reports: string 'true' or 'false'.
 * match_lowercase_tag_field: boolean. If true, then filter rules will always match the lowercase value of the tag_field in the filter rule clauses. For example if the rule matches the tag name of "Test" then a clause will be added to match the tag name of "test" as well.
 * match_lowercase_tag_val: boolean. Same as match_lowercase_tag_field but for the values of the tag instead of the tag name.
 * rules: A list of rule mappings.
 * merges: If a perspective contains a `categorize` rule then a list of merge mappings can be provided to merge Dynamic Groups.

Each rule is a YAML mapping, with two types of rules `filter` and `categorize`.

`filter` rules have the following keys:

 * type: either `filter` or `search`
 * asset: either a string of a valid asset type or a list of valid asset types. Some asset types may not make sense together in the same rule.
 * to: The name of the perspective group that resources matching this rule should be assigned to. New groups will be created as needed.
 * condition: A YAML mapping with the following keys:
   * clauses: a list of clauses. It's really best to just go look at examples in `tests/perspective_data/specs` for what clauses look like. There can be nuances from one clause type to another, so it's best to create the rule in web GUI and then export the spec and see how it has been generated.
   * combine_with: required and only allowed if the list of clauses include more than one item. Set to either OR or AND (uppercase) based on how you want the clauses evaluated.

**Warning:** CloudHealth Perspectives API does not support deleting perspective groups via the API. Groups that should be deleted via the API will have their associated rules deleted, this will cause them to appear aqua green the Web UI making it easy to identify what should be removed manually.

`categorize` rules have the following keys for categorizing by tag. If you want to categorize by something else, then create the rule in web GUI and then export the spec and see how it's been generated.
 * type: `categorize`
 * asset: a string of a valid asset type (list not supported here for now, not sure API will support).
 * to: The name of the perspective group resources matching this rule should be assigned to. New groups will be created as needed. Should be set to be the same as `name`.
 * name: This is the name that will of the perspective group that will be  displayed. Should be the set to be the same as `to`.
 * tag_field: The name of the tag to categorize by.

If a perspective has a one or more `categorize` rules then you may specify mappings defining Dynamic Group merges. Each mapping is to have the following keys.
 * name: The name of the categorize rule that this merge applies to.
 * type: Must be `Group`.
 * to: The name of the Dynamic Group in which the other groups will be merged. This group must exist (i.e. If the Dynamic Groups are based off of tags then CloudHealth must have discovered an asset with that tag and created a Dynamic Group for that tag value).
 * from: A list of Dynamic Groups that will be merged into the Dynamic Group specified by the `to` key. Like the `to` key, the values provide here must match the name of Dynamic Groups that already exist. Either `from` or `from_regex` must be specified (i.e. only one can be specified).
 * from_regex: A list of regexs that will be used to determine what Dynamic Groups should be merged. Any group matching on the regexs will be merged with the group specified by the `to` key. A spec where a group is merged with two different groups will fail to apply. Merges are only evaluated at the time the spec is applied (i.e. either when the perspective is created or updated). The regexs do not necessarily have to match an existing group. Because each Dynamic Group is evaluated at the time the spec is applied you could specify group regexs to match existing and future group. You would then apply the spec on a schedule, such as daily, to merge any newly created groups. Either `from` or `from_regex` must be specified (i.e. only one can be specified).


**Warning:** CloudHealth Perspectives API does not support unmerging groups or changing the group in which a group has already been merged. If you need to unmerge or change the merge configuration (other than merging new groups), then it's recommended to use the `Delete All` button in the CloudHealth web GUI and update the perspective using the new spec.


## Caveats
The goal is for this tool to be somewhat generic, but it has really only been tested for certain use cases specific to deal with AWS resources.
