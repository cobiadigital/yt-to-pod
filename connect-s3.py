import os
import json

def get_keys(path):
        with open(path) as f:
            return json.load(f)

keys = get_keys(".secret/.s3.json")
url = keys['url']
bucket = keys['bucket']

# Set environment variables
os.environ['URL'] = url
os.environ['BUCKET'] = bucket
cwd = os.getcwd()
mountpoint = os.path.join(cwd, 'uploads/')

os.system("s3fs -o passwd_file=.secret/.s3fs-creds -o url=$URL -o use_path_request_style -o endpoint=auto $BUCKET " + mountpoint)