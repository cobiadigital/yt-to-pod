import A03

search = AO3.Search(any_field="", tags="", kudos=AO3.utils.Constraint(30, 5000), fandoms="Original Work", word_count=AO3.utils.Constraint(5000, 15000))
search.update()
print(search.total_results)

search.results[4].id
work = AO3.Work(search.results[4].id)

for chapter in work.chapters:
    print(chapter.title)

text = work.chapters[0].text

with open(f"book6.epub", "wb") as file:
    file.write(work.download("HTML"))



import requests

deploymentsEndpoint = "https://api.cloudflare.com/client/v4/accounts/{account_id}/pages/projects/{project_name}/deployments"
projectEndpoint = "https://api.cloudflare.com/client/v4/accounts/{account_id}/pages/projects/{project_name}"

import http.client

conn = http.client.HTTPSConnection("api.cloudflare.com")
import os
from dotenv import load_dotenv
load_dotenv()

with open('upload/rss.xml') as file:
    payload = file.read()
# payload = "{\n  \"deployment_configs\": {\n    \"production\": {\n      \"compatibility_date\": \"2022-01-01\",\n      \"compatibility_flags\": [\n        \"url_standard\"\n      ],\n      \"env_vars\": {\n        \"BUILD_VERSION\": {\n          \"value\": \"3.3\"\n        },\n        \"delete_this_env_var\": null,\n        \"secret_var\": {\n          \"type\": \"secret_text\",\n          \"value\": \"A_CMS_API_TOKEN\"\n        }\n      }\n    }\n  }\n}"

headers = {
    'Content-Type': "application/json",
    'X-Auth-Email': "ben.brenner@gmail.com"
    }

conn.request("PATCH", f"/client/v4/accounts/{os.getenv('ACCESS_KEY_ID')}/pages/projects/archivepod", payload, headers)

res = conn.getresponse()
data = res.read()

print(data.decode("utf-8"))