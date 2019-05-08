import json

def replace_siteid(uploadid, json_file):
    #step-1: find the siteid from jsonfile
    with open(json_file, 'r') as jsonfile:
        data = json.load(jsonfile)
        for x in data:
            for y in x.keys():
                if 'site' == y:
                    print ('****** Congratus! site-id is found  ****** ')
                    siteref = x['id']
                else:
                    pass

    #step-2: replace the siteid with uploadid
    for x in data:
        for y in x.keys():
            if 'siteRef'== y:
                x['siteRef'] = 'r:' + uploadid
            elif 'site' == y:
                x['id'] = 'r:' + uploadid
            else:
                pass

    #step-3: replace the old json file with updated jsonfile
    with open(json_file,'w') as jsonfile_updated:
        json.dump(data, jsonfile_updated)

