def send_reading_requests(point_id_readable):
    '''
    Purpose: receive responses of http-reading-requests for Haystack point
    Inputs: point_id_readable
    Returns: http-reading-request status
    Notes: url ="http://localhost:80/api/read"; header and data need to follow Haystack syntax
    '''
    url = "http://localhost:80/api/read"
    header = {"Accept": "application/json", "Content-Type": "text/zinc"}
    data = """ver:"2.0"
            filter,limit
            \"id==@""" + point_id_readable + r"\,1000"

    reading_response = requests.post(url=url, headers=header, data=data)

    print(reading_response)


def send_writing_requests(point_id_writable):
    '''
    Purpose: receive responses of http-writing-requests for Haystack point
    Inputs: point_id_writable
    Returns: http-writing-request status
    Notes: url ="http://localhost:80/api/pointWrite"; header and data need to follow Haystack syntax
    '''
    url = "http://localhost:80/api/pointWrite"
    header = {"Accept": "application/json", "Content-Type": "application/json; charset=utf-8"}
    data = json.dumps(
        {
            "meta": {"ver": "2.0"},
            "rows": [{"id": "r:" + point_id_writable,
                      "level": "n:1",
                      "who": "s:",
                      "val": "n:0.5",
                      "duration": "s:"
                      }
                     ],
            "cols": [{"name": "id"}, {"name": "level"}, {"name": "val"}, {"name": "who"}, {"name": "duration"}]
        }
    )

    writing_response = requests.post(url=url, headers=header, data=data)

    print(writing_response)
