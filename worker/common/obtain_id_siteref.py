import json

def revise_id_siteref(jsonpath):
    '''
    Purpose: remove the r: from the site id in json file
    Inputs: json file path
    Returns: revised id string for site
    '''
    site_ref = ''
    with open(jsonpath) as json_file:
        data = json.load(json_file)
        for entity in data:
            if 'site' in entity:
                if entity['site'] == 'm:':
                    site_ref = entity['id'].replace('r:', '')
                    break

    return site_ref
