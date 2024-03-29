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

def create_work_item(work_item_data, parent_id=None, new_epic_name=None, relationships=[], parent_id_mapping={}) -> Dict[int, int]:
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
        'Microsoft.VSTS.Scheduling.StoryPoints',
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
    # Handle predecessor and successor relationships
    for relation in relationships:
        rel_type = relation.get('rel')
        if rel_type == 'System.LinkTypes.Dependency-Reverse' or rel_type == 'System.LinkTypes.Dependency-Foward':
            old_related_work_item_id = int(relation['url'].split('/')[-1])

            # Ensure the old_related_work_item_id is in parent_id_mapping
            if old_related_work_item_id in parent_id_mapping:
                new_related_work_item_id = parent_id_mapping[old_related_work_item_id]
                comment = relation.get('attributes', {}).get('comment', None)

                # Now use this comment in your patch_data.append call
                patch_data.append({
                    'op': 'add',
                    'path': '/relations/-',
                    'value': {
                        'rel': rel_type,
                        'url': f'https://dev.azure.com/{organization}/{project}/_apis/wit/workItems/{new_related_work_item_id}',
                        'attributes': {
                            'comment': comment
                        }
                    }
                })
            else:
                print(f"Warning: old_related_work_item_id {old_related_work_item_id} not found in parent_id_mapping. Skipping relation.")


    work_item_type = work_item_fields['System.WorkItemType']
    url = f'https://dev.azure.com/{organization}/{project}/_apis/wit/workitems/${work_item_type}?api-version=6.0'
    response = requests.patch(url, headers=headers, json=patch_data)
    response_data = response.json()
    # Debugging lines
    # print("Response Status:", response.status_code)
    # print("Response Data:", response_data)
    

    if "id" not in response_data:
        print("Error: ID not found in the response.")
        return
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

            # Extract relationships from the original work item
            relationships = work_item_data.get('relations', [])

            parent_id = None
            if 'System.Parent' in work_item_data['fields']:
                old_parent_id = work_item_data['fields']['System.Parent']
                if old_parent_id in parent_id_mapping:
                    parent_id = parent_id_mapping[old_parent_id]

            new_work_item = create_work_item(work_item_data, parent_id, new_epic_name, relationships, parent_id_mapping)
            parent_id_mapping.update(new_work_item)

    print('Parent ID Mapping:', parent_id_mapping)
    return parent_id_mapping

def main():
    folder_path = "output"
    new_epic_name = input("Please enter the new epic name: ")
    create_work_items_from_folder(folder_path, new_epic_name)

if __name__ == "__main__":
    main()
