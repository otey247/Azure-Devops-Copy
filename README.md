# Azure Work Item Migration

This repository contains two Python scripts to help you migrate Azure DevOps work items while preserving their parent-child relationships.

## Prerequisites

- Python 3.x
- `requests` library for Python

You can install the `requests` library using the following command:

```bash
pip install requests
```

## Usage

### Step 1: Save Work Items to JSON Files

1. Open `Folder Save.py` and provide the following information:
   - `organization`: Your Azure DevOps organization name
   - `project`: Your Azure DevOps project name
   - `pat`: Your Personal Access Token (PAT) for authentication

2. Set the `epic` variable to the top-level work item ID (usually an Epic ID) you want to migrate.

3. Run `Folder Save.py`:

```bash
python Folder Save.py
```

This script will save the work items and their children as JSON files in the `output` folder.

### Step 2: Create New Work Items in Azure DevOps

1. Open `New App.py` and provide the following information:
   - `organization`: Your Azure DevOps organization name
   - `project`: Your Azure DevOps project name
   - `pat`: Your Personal Access Token (PAT) for authentication

2. Run `New App.py`:

```bash
python New App.py
```

This script will read the JSON files from the `output` folder, create new work items in Azure DevOps, and maintain the parent-child relationships between the new work items as they were in the old work items. The script will also print the parent ID mapping between the old work items and the new work items.
