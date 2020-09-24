import os
import requests
from pprint import pprint
from flask import Flask, request, Response

app = Flask(__name__)

# Start with
# SENDINBLUE_API_KEY=<key> python3 tools/sendinblueAPIPlayground.py 

LISTES_ECOSANTE_FOLDER_NAME = 'listes_ecosante'

api_key = os.environ['SENDINBLUE_API_KEY'] # Will throw if none if found and that's ok
pprint('API key: {}'.format(api_key))

SENDINBLUE_DEFAULT_GET_HEADERS = {"accept": "application/json", "api-key": api_key}
SENDINBLUE_DEFAULT_POST_HEADERS = {"accept": "application/json", "content-type": "application/json", "api-key": api_key}


@app.route('/', methods=['GET'])
def respond():
    print(request.query_string)
    return Response(response="coucou !", status=200)




def onListImported(request):
    print('YAY, list was imported!')
    pprint(request.body)

webhook_dict = dict()
webhook_dict['onListImported'] = onListImported



@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    print('# WEBHOOK #')
    pprint(f'secret: {request.args.get("secret")}')
    
    fun = webhook_dict[request.args.get("secret")]

    fun(request)

    return Response(response="thank you!", status=202)



@app.route('/run', methods=['GET'])
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
        "notifyUrl": "http://app-5eedd47c-0ebb-4933-8c82-edcf2ed13a66.cleverapps.io/webhook?secret=onListImported"
    }

    r_import = requests.request("POST", "https://api.sendinblue.com/v3/contacts/import", json=payload, headers=SENDINBLUE_DEFAULT_POST_HEADERS)
    r_import.raise_for_status()
    ## HTTP Status should be 202 Accepted

    return Response(response="<a href=\"https://console.clever-cloud.com/organisations/orga_35c34f04-1a7a-4fdf-b5bf-77b58d7540de/applications/app_5eedd47c-0ebb-4933-8c82-edcf2ed13a66/logs\">LOGS</a>", status=202)


