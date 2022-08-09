# File to store some mock data for testing mongodb connections
site_data = [
    {
        "ref_id": "123",
        "name": "Test Building in Random Geographic Place",
        "dis": "s:Building 1",
        "geo_city": "s:Random Geographic Place",
    },
    {
        "ref_id": "456",
        "name": "Test Building 2 in Random Geographic Place and Haystack Data",
        "dis": "s:Building 2",
        "geo_city": "s:Random Geographic Place",
        "geo_coord": "c:39.83,-84.05",
        "haystack_raw": [
            {
                "id": "r:site_456_rec_1",
                "geoCity": "s:Dayton Wright Patterson Afb",
                "geoCoord": "c:39.83,-84.05",
            },
            {
                "id": "r:site_456_rec_2",
                "dis": "s:HVAC Cooling Power",
                "siteRef": "r:456",
                "curStatus": "s:disabled"
            }
        ]
    }
]

rec_data = [
    {
        "site_id": "456",
        "ref_id": "site_456_rec_1",
        "rec": {
            "id": "r:site_456_rec_1",
            "geoCity": "s:Dayton Wright Patterson Afb",
            "geoCoord": "c:39.83,-84.05",
        }
    },
    {
        "site_id": "456",
        "ref_id": "site_456_rec_2",
        "rec": {
            "id": "r:site_456_rec_2",
            "dis": "s:HVAC Cooling Power",
            "siteRef": "r:456",
            "curStatus": "s:disabled"
        }
    }
]
