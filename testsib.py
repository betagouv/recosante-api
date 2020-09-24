import os
import requests
from pprint import pprint

# Start with
# SENDINBLUE_API_KEY=<key> python3 tools/sendinblueAPIPlayground.py 

LISTES_ECOSANTE_FOLDER_NAME = 'listes_ecosante'

api_key = os.environ['SENDINBLUE_API_KEY'] # Will throw if none if found and that's ok
pprint('API key: {}'.format(api_key))

SENDINBLUE_DEFAULT_GET_HEADERS = {"accept": "application/json", "api-key": api_key}
SENDINBLUE_DEFAULT_POST_HEADERS = {"accept": "application/json", "content-type": "application/json", "api-key": api_key}

def run():
    print("Hurray!")
    # Get relevant folder id

    r_folder = requests.get('https://api.sendinblue.com/v3/contacts/folders', headers=SENDINBLUE_DEFAULT_GET_HEADERS)
    r_folder.raise_for_status()

    folders = r_folder.json()['folders']

    listes_ecosante_folder_id = [folder for folder in folders if folder['name'] == LISTES_ECOSANTE_FOLDER_NAME][0]['id']

    pprint(f'folder id for "{LISTES_ECOSANTE_FOLDER_NAME}" is "{listes_ecosante_folder_id}"')
        

    # Import list in folder
    csv_file = open("./data/fake-Tous-les-jours-Mail.csv", 'r').read()

    pprint(csv_file)

    import_payload = {
        "emailBlacklist": False,
        "smsBlacklist": False,
        "updateExistingContacts": True,
        "emptyContactsAttributes": False,
        "fileBody": csv_file,
        "newList": {
            "name": "test-api-list-by-davbru",
            "folder_id": listes_ecosante_folder_id
        }
        #notifyUrl
    }

    # r_import = requests.request("POST", "https://api.sendinblue.com/v3/contacts/import", json=payload, headers=SENDINBLUE_DEFAULT_POST_HEADERS)
    # r_import.raise_for_status()
    # # HTTP Status should be 202 Accepted

    # new_list_id = r_import.json()

    # pprint(f'List creation from csv is a success! list id: id for "{LISTES_ECOSANTE_FOLDER_NAME}" is "{listes_ecosante_folder_id}"')
