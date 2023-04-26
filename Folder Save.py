import requests
import json
import base64
import os

organization = ''
project = ''
pat = ''
authorization = str(base64.b64encode(bytes(':'+pat, 'ascii')), 'ascii')

headers = {
    'Accept': 'application/json',
    'Authorization': 'Basic '+authorization
}

# Create a new folder named 'output'
output_dir = 'output'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

def get_work_item(id):
    url = f'https://dev.azure.com/{organization}/{project}/_apis/wit/workitems/{id}?api-version=6.0&$expand=relations'
    response = requests.get(url, headers=headers)
    data = response.json()

    # Save JSON object to a file with the top-level "id" as the filename
    with open(os.path.join(output_dir, f'{id}.json'), 'w') as file:
        json.dump(data, file, indent=2)

    if 'relations' in data:
        for relation in data['relations']:
            if relation['rel'] == 'System.LinkTypes.Hierarchy-Forward':
                child_id = relation['url'].split('/')[-1]
                get_work_item(child_id)

epic = 1
get_work_item(epic)
