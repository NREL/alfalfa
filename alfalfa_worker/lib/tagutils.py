import json
import uuid

def replace_site_id(uploadid, points_json):
    for x in points_json:
        for y in x.keys():
            if 'siteRef' == y:
                x['siteRef'] = 'r:' + uploadid
            elif 'site' == y:
                x['id'] = 'r:' + uploadid
            else:
                pass

    return points_json

def make_ids_unique(points_json, mapping_json):
    # map of old id to new id
    idmap = {}

    # iterate all points and make a map of old id to new id
    for point in points_json:
        if "id" in point:
            oldid = point["id"]
            newid = "r:%s" % str(uuid.uuid1())
            idmap[oldid] = newid

    # now use map to update all references to old id
    for point in points_json:
        for tag, oldvalue in point.items():
            if oldvalue in idmap:
                point[tag] = idmap[oldvalue]

    for point in mapping_json:
        if "id" in point:
            oldid = point["id"]
            if oldid in idmap:
                point["id"] = idmap[oldid]

    return points_json, mapping_json

