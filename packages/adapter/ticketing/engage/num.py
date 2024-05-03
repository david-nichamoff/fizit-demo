import requests
import json

proof_dict = {
        "hash" : "",
        "mimeType" : "",
        "timestamp" : "" }

info_dict = {
        "provider" : "Capture API",
        "name" : "version",
        "value" : "v3" }

meta_dict = {
        "proof" : proof_dict,
        "information" : [ info_dict ] }

caption = 'This is an example caption'
headline = 'This is an example headline'
headers = {'Authorization' : 'token 74526ed6d6ee01113b0ddf20abdb023ba0268830' }
files = { "asset_file" : ("test.pdf", open("/home/ec2-user/engage/ticket/881077.pdf","rb"))}

numbers_resp = requests.post(f'https://api.numbersprotocol.io/api/v3/assets/', headers=headers, files=files,
                            data = { 'meta' : meta_dict,
                                     'caption' : caption,
                                     'headline' : headline })

print(numbers_resp.text)
print(numbers_resp.json())
numbers_dict = json.loads(numbers_resp.text)
print(numbers_dict)
print(numbers_dict['error'])
