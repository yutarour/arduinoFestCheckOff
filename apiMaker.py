import requests

ses = requests.Session()
ENDPOINT = "https://csclub.uwaterloo.ca/~phthakka/1pt-express/addURL"
URLTOSHORTEN = ""
resp = ses.post(ENDPOINT,verify=False,params={"long":URLTOSHORTEN})
respjs = resp.json()
print(f"https://1pt.co/{respjs['short']}")
#{'message': 'Added!', 'short': '7pwrp', 'long': 'https://example.com'}
