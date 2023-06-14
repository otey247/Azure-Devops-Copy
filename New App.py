import os
import requests
import json
import base64
from typing import Dict

organization = ''
project = ''
pat = ''
authorization = str(base64.b64encode(bytes(':'+pat, 'ascii')), 'ascii')

headers = {
    'Content-Type': 'application/json-patch+json',
    'Authorization': 'Basic '+authorization
}

def create_work_item(work_item_data, parent_id=None, new_epic_name=None) -> Dict[int, int]:
    work_item_fields = work_item_data['fields']
    work_item_type = work_item_fields['System.WorkItemType']
    
    if new_epic_name and work_item_type == "Epic":
        work_item_fields['System.Title'] = new_epic_name
        
    if work_item_fields.get('System.Tags'):
        work_item_fields['System.Tags'] += f"; {new_epic_name}"
    else:
        work_item_fields['System.Tags'] = new_epic_name

    field_keys = [
        'System.AreaPath',
        'System.TeamProject',
        'System.WorkItemType',
        'System.Title',
        'Microsoft.VSTS.Common.Priority',
        'Microsoft.VSTS.Common.ValueArea',
        'Microsoft.VSTS.Scheduling.Effort',
        'System.Description',
        'System.Tags',
        'System.Parent'
    ]

    patch_data = []
    for key in field_keys:
        if key in work_item_fields:
            patch_data.append({
                'op': 'add',
                'path': f'/fields/{key}',
                'value': work_item_fields[key]
            })

    if parent_id:
        patch_data.append({
            'op': 'add',
            'path': '/relations/-',
            'value': {
                'rel': 'System.LinkTypes.Hierarchy-Reverse',
                'url': f'https://dev.azure.com/{organization}/{project}/_apis/wit/workItems/{parent_id}',
                'attributes': {
                    'comment': 'Relates to'
                }
            }
        })

    work_item_type = work_item_fields['System.WorkItemType']
    url = f'https://dev.azure.com/{organization}/{project}/_apis/wit/workitems/${work_item_type}?api-version=6.0'
    response = requests.patch(url, headers=headers, json=patch_data)
    response_data = response.json()
    new_work_item_id = response_data['id']
    old_work_item_id = work_item_data['id']
    return {old_work_item_id: new_work_item_id}

def create_work_items_from_folder(folder_path: str, new_epic_name: str) -> Dict[int, int]:
    parent_id_mapping = {}

    # Define a function to sort work items by their WorkItemType
    def work_item_sort_key(file_name):
        with open(os.path.join(folder_path, file_name), 'r') as f:
            work_item_data = json.load(f)
            work_item_type = work_item_data['fields']['System.WorkItemType']
            return {'Epic': 1, 'Feature': 2, 'User Story': 3, 'Task': 4}.get(work_item_type, 5)

    sorted_files = sorted(filter(lambda file: file.endswith('.json'), os.listdir(folder_path)), key=work_item_sort_key)

    for file in sorted_files:
        file_path = os.path.join(folder_path, file)

        with open(file_path, 'r') as f:
            work_item_data = json.load(f)

            parent_id = None
            if 'System.Parent' in work_item_data['fields']:
                old_parent_id = work_item_data['fields']['System.Parent']
                if old_parent_id in parent_id_mapping:
                    parent_id = parent_id_mapping[old_parent_id]

            new_work_item = create_work_item(work_item_data, parent_id, new_epic_name)
            parent_id_mapping.update(new_work_item)

    print('Parent ID Mapping:', parent_id_mapping)
    return parent_id_mapping

def main():
    folder_path = "output"
    new_epic_name = input("Please enter the new epic name: ")
    create_work_items_from_folder(folder_path, new_epic_name)

if __name__ == "__main__":
    main()
