import requests
import json
import env_var
import os

env_var = env_var.get_env()

artifact_path = os.environ['PYTHONPATH'] + '/../artifacts/0/'
artifact_files = next(os.walk(artifact_path))[2]
proof_dict = { "hash" : "", "mimeType" : "", "timestamp" : "" }
info_dict = { "provider" : "FIZIT", "name" : "test", "value" : "0" }
meta_dict = { "proof" : proof_dict, "information" : [ info_dict ] }
header_dict = {'Authorization' : 'token ' + str(env_var["numbers_key"]) }
print 

for artifact_file in artifact_files:
    caption = str(0) + ": " + str(artifact_file)
    file_dict = { "asset_file" : (artifact_file, open(artifact_path + str(artifact_file),"rb"))}
    print (file_dict)
    print (header_dict)
    response = requests.post(env_var["numbers_url"], headers=header_dict, files=file_dict, data = { 'meta' : meta_dict, 'caption' : caption, 'public_access' : False})
    print(response)
