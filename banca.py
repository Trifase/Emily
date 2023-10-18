import json
import os.path
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests
from requests.models import HTTPError
from requests.structures import CaseInsensitiveDict
from rich import box
from rich.table import Table
from telegram import Update
from telegram.ext import ContextTypes
# test cherry pick
import config
from utils import printlog

# BANK_ID = "BANCA_CARIGE_CRGEITGG"
BANK_ID = "BPER_RETAIL_BPMOIT22"
SECRET_ID = config.SECRET_ID
SECRET_KEY = config.SECRET_KEY
redirect = "http://www.morsmordre.it"

def get_new_token(secret_id, secret_key):
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
    }

    data = {
        "secret_id": secret_id,
        "secret_key": secret_key
        }

    response = requests.post('https://ob.nordigen.com/api/v2/token/new/', headers=headers, json=data)

    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()

def refresh_token(refresh_token):

    url = "https://ob.nordigen.com/api/v2/token/refresh/"

    headers = CaseInsensitiveDict()
    headers["accept"] = "application/json"
    headers["Content-Type"] = "application/json"

    data = {
        "refresh": refresh_token
        }


    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()

def get_or_refresh_token(SECRET_ID, SECRET_KEY):
    if os.path.isfile(f'banca/{SECRET_ID}.json'):  # c'è già un file token con questo ID
        with open(f'banca/{SECRET_ID}.json') as json_file:
            data = json.load(json_file)

        refresh = data['refresh']  # refresho
        try:
            newdata = refresh_token(refresh)
            data['access'] = newdata['access']
            with open(f'banca/{SECRET_ID}.json', 'w') as outfile:  # scrivo il nuovo token
                json.dump(data, outfile)
        except HTTPError:  # il refresh token è scaduto/invalido
            print("Errore. Refresh token scaduto. Genero tutto da capo..")
            data = get_new_token(SECRET_ID, SECRET_KEY)
            with open(f'banca/{SECRET_ID}.json', 'w') as outfile:
                json.dump(data, outfile)

    else:  # non c'è un file token
        data = get_new_token(SECRET_ID, SECRET_KEY)  # ne creo uno

        with open(f'banca/{SECRET_ID}.json', 'w') as outfile:
            json.dump(data, outfile)

    return data['access']  # in ogni caso ritorna il token refreshato o nuovo

def build_requisition(token, BANK_ID, redirect_url="http://www.google.com"):  # returns link, requisition_id

    url = "https://ob.nordigen.com/api/v2/requisitions/"

    headers = CaseInsensitiveDict()
    headers["accept"] = "application/json"
    headers["Content-Type"] = "application/json"
    headers["Authorization"] = f"Bearer {token}"

    data = {
        "redirect": redirect_url,
        "institution_id": BANK_ID
        }


    response = requests.post(url, headers=headers, json=data)

    if response.ok:
        response = response.json()
        # print("====")
        # print(response)
        # print("====")
        link = response['link']
        requisition_id = response['id']
        return link, requisition_id
    else:
        print(f"Errore! {response.status_code}")
        raise HTTPError

def get_requisition_list(token):

    url = "https://ob.nordigen.com/api/v2/requisitions/"

    headers = CaseInsensitiveDict()
    headers["accept"] = "application/json"
    headers["Authorization"] = f"Bearer {token}"


    response = requests.get(url, headers=headers)
    if response.ok:
        return response.json()
    else:
        print(f"Errore! {response.status_code}")
        response.raise_for_status()
        raise HTTPError

def delete_requisition(token, uuid):

    url = f"https://ob.nordigen.com/api/v2/requisitions/{uuid}"

    headers = CaseInsensitiveDict()
    headers["accept"] = "application/json"
    headers["Authorization"] = f"Bearer {token}"


    response = requests.delete(url, headers=headers)
    if response.ok:
        return response.json()
    else:
        print(f"Errore! {response.status_code}")
        response.raise_for_status()
        raise HTTPError

def get_account_id_from_api(token, requisition_id):

    url = f"https://ob.nordigen.com/api/v2/requisitions/{requisition_id}/"
    headers = CaseInsensitiveDict()
    headers["accept"] = "application/json"
    headers["Authorization"] = f"Bearer {token}"


    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        response = response.json()
        # account_id = response['accounts'][0]
        return response
    else:
        response.raise_for_status()


def get_banks(token, country_code="it"):

    url = f"https://ob.nordigen.com/api/v2/institutions/?country={country_code}"

    headers = CaseInsensitiveDict()
    headers["accept"] = "application/json"
    headers["Authorization"] = f"Bearer {token}"


    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()

def refresh_requisition(token):
    with open('banca/accounts.json') as account_file:
        data = json.load(account_file)
        bank_id = data['bank_id']
        account_dict = dict()
        link, requisition_id = build_requisition(token, bank_id, "http://127.0.0.1:12666")  # creo un agreement


        class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.wfile.write(b'Grazie, puoi chiudere!')

                threading.Thread(target=httpd.shutdown, daemon=True).start()

        httpd = HTTPServer(('localhost', 12666), SimpleHTTPRequestHandler)

        print("Apri il seguente link, segui la procedura per autenticarti con la banca (user: 11082651):")
        print(link)
        httpd.serve_forever()
        print("Fatto!")
        account_dict['bank_id'] = bank_id
        account_dict['requisition_id'] = requisition_id
        response = get_account_id_from_api(token, requisition_id)

        acc_id = response['accounts'][0]
        account_dict['acc_id'] = acc_id
        with open('banca/accounts.json', 'w') as outfile:
            json.dump(account_dict, outfile)
        return acc_id

def get_account_id(token, BANK_ID, redirect):
    if os.path.isfile('banca/accounts.json'):  # c'è già un file per gli account
        with open('banca/accounts.json') as json_file:
            data = json.load(json_file)

        acc_id = data['acc_id']
        requisition_id = data['requisition_id']
        return acc_id
    else:  # non c'è un file accounts
        account_dict = dict()
        link, requisition_id = build_requisition(token, BANK_ID, "http://127.0.0.1:12666")  # creo un agreement



        class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.wfile.write(b'Grazie, puoi chiudere!')

                threading.Thread(target=httpd.shutdown, daemon=True).start()

        httpd = HTTPServer(('localhost', 12666), SimpleHTTPRequestHandler)

        print("Apri il seguente link, segui la procedura per autenticarti con la banca (user: 11082651):")
        print(link)
        httpd.serve_forever()
        print("Fatto!")
        account_dict['bank_id'] = BANK_ID
        account_dict['requisition_id'] = requisition_id
        response = get_account_id_from_api(token, requisition_id)

        acc_id = response['accounts'][0]
        account_dict['acc_id'] = acc_id
        with open('banca/accounts.json', 'w') as outfile:
            json.dump(account_dict, outfile)
        return acc_id

def get_transactions(token, acc_id):

    url = f"https://ob.nordigen.com/api/v2/accounts/{acc_id}/transactions/"

    headers = CaseInsensitiveDict()
    headers["accept"] = "application/json"
    headers["Authorization"] = f"Bearer {token}"


    response = requests.get(url, headers=headers)
    if response.ok:
        return response.json()
    elif response.status_code == 400:  # requisition scaduta
        new_acc_id = refresh_requisition(token)
        return get_transactions(token, new_acc_id)
    else:
        response.raise_for_status()

def get_saldo(token, acc_id, just_the_number=1):

    url = f"https://ob.nordigen.com/api/v2/accounts/{acc_id}/balances/"

    headers = CaseInsensitiveDict()
    headers["accept"] = "application/json"
    headers["Authorization"] = f"Bearer {token}"


    response = requests.get(url, headers=headers)
    if response.ok:
        if just_the_number == 1:
            response = response.json()
            return response['balances'][1]['balanceAmount']['amount']
        else:
            return response.json()
    elif response.status_code == 400:  # requisition scaduta
        new_acc_id = refresh_requisition(token)
        return get_transactions(token, new_acc_id)
    else:
        response.raise_for_status()

def transactions_nice_table(token, acc_id):

    table = Table(title="Lista Transazioni", box=box.SQUARE_DOUBLE_HEAD)

    table.add_column("Data")
    table.add_column("Importo", justify="right")
    table.add_column("Causale")

    for t in get_transactions(token, acc_id)['transactions']['booked']:
        # print(f"{t['bookingDate']}\t{t['transactionAmount']['amount']}€\t{t['remittanceInformationUnstructured']}")
        table.add_row(t['bookingDate'], f"{t['transactionAmount']['amount']}€", t['remittanceInformationUnstructured'])

    return(table)

async def bot_get_saldo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in config.ADMINS:
        return
    # print("saldo")
    # BANK_ID = "BANCA_CARIGE_CRGEITGG"
    BANK_ID = "BPER_RETAIL_BPMOIT22"
    SECRET_ID = config.SECRET_ID
    SECRET_KEY = config.SECRET_KEY
    redirect = "http://www.morsmordre.it"

    token = get_or_refresh_token(SECRET_ID, SECRET_KEY)
    # print("token ok")
    acc_id = get_account_id(token, BANK_ID, redirect)
    # print("acc_id ok")
    await printlog(update, "chiede il saldo della banca")
    await update.message.reply_text(f"{get_saldo(token, acc_id, 1)} €")

async def bot_get_transazioni(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in config.ADMINS:
        return
    # print("saldo")
    # BANK_ID = "BANCA_CARIGE_CRGEITGG"
    BANK_ID = "BPER_RETAIL_BPMOIT22"
    SECRET_ID = config.SECRET_ID
    SECRET_KEY = config.SECRET_KEY
    redirect = "http://www.morsmordre.it"
    messaggio = ""
    token = get_or_refresh_token(SECRET_ID, SECRET_KEY)
    # print("token ok")
    acc_id = get_account_id(token, BANK_ID, redirect)
    try:
        n = int(context.args[0])
    except IndexError:
        n = 5
    # print("acc_id ok")
    messaggio += f"Ultime {n} transazioni:\n"
    for t in get_transactions(token, acc_id)['transactions']['booked'][:n]:
        messaggio += f"[{t['transactionAmount']['amount']} €] {t['remittanceInformationUnstructured']}\n------\n"
    await printlog(update, "chiede i movimenti bancari")
    await update.message.reply_text(messaggio)
