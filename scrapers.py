import requests

import pprint

async def file_in_limits(url, debug=False) -> bool:
    info = requests.head(url)
    if "mp4" in info.headers["Content-Type"]:
        if int(info.headers["Content-Length"]) <= 20000000:
            if debug:
                print(url)
                print("E' nei limiti")
                pprint.pprint(info.headers)
            return True

    if "image" in info.headers["Content-Type"]:
        if int(info.headers["Content-Length"]) <= 5000000:
            if debug:
                print(url)
                pprint.pprint(info.headers)
                print("E' nei limiti")
            return True

    if debug:
        print(url)
        pprint.pprint(info.headers)
        print("Non è nei limiti")
    return False
