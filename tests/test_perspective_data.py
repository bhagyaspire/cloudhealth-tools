from deepdiff import DeepDiff

from chtools.perspective.data import Perspective


def test_catagorize_grou_merge():
    perspective = Perspective(None)
    perspective.id = '2954937503983'
    # set initial schema
    perspective.schema = {'name': 'Environments', 'include_in_reports': 'true',
                          'rules': [{'type': 'categorize', 'asset': 'AwsAsset',
                                     'tag_field': ['Environment'],
                                     'ref_id': '2954937505877',
                                     'name': 'Environments'}], 'merges': [],
                          'constants': [{'type': 'Dynamic Group Block',
                                         'list': [{'ref_id': '2954937505877',
                                                   'name': 'Environments'}]},
                                        {'type': 'Dynamic Group', 'list': [
                                            {'ref_id': '2954937647846',
                                             'blk_id': '2954937505877',
                                             'val': 'Development',
                                             'name': 'Development'},
                                            {'ref_id': '2954937647847',
                                             'blk_id': '2954937505877',
                                             'val': 'Live', 'name': 'Live'},
                                            {'ref_id': '2954937647850',
                                             'blk_id': '2954937505877',
                                             'val': 'Production',
                                             'name': 'Production'},
                                            {'ref_id': '2954937647851',
                                             'blk_id': '2954937505877',
                                             'val': 'Integration Testing',
                                             'name': 'Integration Testing'},
                                            {'ref_id': '2954937647853',
                                             'blk_id': '2954937505877',
                                             'val': 'live', 'name': 'live'}]},
                                        {'type': 'Static Group', 'list': [
                                            {'ref_id': '2954937647845',
                                             'name': 'Other',
                                             'is_other': 'true'}]}]}
    # Apply spec with merges
    perspective.spec = {'include_in_reports': 'true', 'merges': [
        {'from': ['Live', 'live'], 'name': 'Environments', 'to': 'Production',
         'type': 'Group'}], 'name': 'Environments', 'rules': [
        {'asset': 'AwsAsset', 'name': 'Environments',
         'tag_field': 'Environment', 'to': 'Environments',
         'type': 'categorize'}]}

    expected_schema = {'name': 'Environments', 'include_in_reports': 'true',
                       'rules': [{'asset': 'AwsAsset', 'name': 'Environments',
                                  'tag_field': ['Environment'],
                                  'type': 'categorize',
                                  'ref_id': '2954937505877'}], 'merges': [
            {'type': 'Group', 'to': '2954937647850',
             'from': ['2954937647847', '2954937647853']}], 'constants': [
            {'type': 'Dynamic Group Block',
             'list': [{'ref_id': '2954937505877', 'name': 'Environments'}]},
            {'type': 'Dynamic Group', 'list': [
                {'ref_id': '2954937647846', 'blk_id': '2954937505877',
                 'val': 'Development', 'name': 'Development'},
                {'ref_id': '2954937647847', 'blk_id': '2954937505877',
                 'val': 'Live', 'name': 'Live', 'fwd_to': '2954937647850'},
                {'ref_id': '2954937647850', 'blk_id': '2954937505877',
                 'val': 'Production', 'name': 'Production'},
                {'ref_id': '2954937647851', 'blk_id': '2954937505877',
                 'val': 'Integration Testing', 'name': 'Integration Testing'},
                {'ref_id': '2954937647853', 'blk_id': '2954937505877',
                 'val': 'live', 'name': 'live', 'fwd_to': '2954937647850'}]},
            {'type': 'Static Group', 'list': [
                {'ref_id': '2954937647845', 'name': 'Other',
                 'is_other': 'true'}]}]}

    differences = DeepDiff(expected_schema, perspective.schema)
    assert differences == {}, (
        "DeepDiff reports the following differences between expected schema "
        "and generated schema: {}".format(differences)
    )
