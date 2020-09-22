import os
import requests
from pprint import pprint

listes_ecosante_folder_name = 'listes_ecosante'

# Start with
# SENDINBLUE_API_KEY=<key> python3 tools/sendinblueAPIPlayground.py 

if __name__ == "__main__":
    api_key = os.environ['SENDINBLUE_API_KEY']
    pprint('API key: {}'.format(api_key))
    sendinblue_default_headers = {"accept": "application/json", "api-key": api_key}

    r = requests.get('https://api.sendinblue.com/v3/contacts/folders', headers=sendinblue_default_headers)
    pprint(r.status_code)

    folders = r.json()['folders']

    listes_ecosante_folder_id = [folder for folder in folders if folder['name'] == listes_ecosante_folder_name][0]['id']

    pprint('folder is for "{}": {}'.format(listes_ecosante_folder_name, listes_ecosante_folder_id))
    
    