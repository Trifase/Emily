from telegram import Update
from telegram.ext import ContextTypes

import config
from utils import printlog
from requests import HTTPError

from nordigen import NordigenClient
from uuid import uuid4

BANK_ID = "BPER_RETAIL_BPMOIT22"
SECRET_ID = config.SECRET_ID
SECRET_KEY = config.SECRET_KEY

def create_new_requisition(client: NordigenClient):
    ref_id = str(uuid4())
    init = client.initialize_session(
        # institution id
        institution_id=BANK_ID,
        # redirect url after successful authentication
        redirect_uri="http://localhost",
        access_valid_for_days=180,
        max_historical_days=90,
        # additional layer of unique ID defined by you
        reference_id=ref_id
    )

    link = init.link # bank authorization link
    requisition_id = init.requisition_id
    return requisition_id, link

async def bot_get_saldo2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in config.ADMINS:
        return

    await printlog(update, "chiede il saldo della banca")

    # prendi il refresh token: se è generato meno di 2592000 secondi, usalo per prendere un nuovo token con new_token = client.exchange_token(token_data["refresh"])
    # altrimenti, genera entrambi i token e salva il refresh token con client.generate_token()
    # OPPURE
    # genera il token direttamente chi se ne frega lmao

    # prendi il requisition_id se lo hai e prova a prendere gli account. se non lo hai, o è scaduto, crea un nuovo requisition di 180gg, manda il link all'utente e salva il requisition id.
    # vedi tu se fare il webserver per continuare automaticamente o chiedere all'utente di riprovare.

    # con il requisition_id, prendi gli account. prendi l'account_id e usalo per generare un account da cui chiedere il balance, con account = client.account_api(id=account_id) e balances = account.get_balances()

    client = NordigenClient(
        secret_id=SECRET_ID,
        secret_key=SECRET_KEY
    )

    client.generate_token()

    # prendere il requisition_id precedentemente salvato
    requisition_id = context.bot_data.get('banca_requisition_id', None)

    if not requisition_id:
        await printlog(update, "chiede il saldo della banca ma non c'è un requisition ID")

        requisition_id, link = create_new_requisition(client)
        # salvare il requisition_id per la prossima volta
        context.bot_data['banca_requisition_id'] = requisition_id

        message = 'Non ho un requisition ID, ne creo uno nuovo, cliccalo e rimanda il comando quando finisci.'
        await update.message.reply_text(message)
        await update.message.reply_text(link)
        return

    try:
        accounts = client.requisition.get_requisition_by_id(requisition_id=requisition_id)
    except HTTPError as e:
        #TODO: capire quale status_code restituisce una requisition scaduta, non lo trovo nella documentazione
        if e.response.status_code == 404 or e.response.status_code == 400:
            await printlog(update, "chiede il saldo della banca ma non c'è un requisition ID")

            # salvare il requisition_id per la prossima volta
            requisition_id, link = create_new_requisition(client)
            context.bot_data['banca_requisition_id'] = requisition_id

            message = 'Il requisition ID è scaduto, ne creo uno nuovo, cliccalo e rimanda il comando quando finisci.'
            await update.message.reply_text(message)
            await update.message.reply_text(link)
            return

        else:
            print(e)
            print(e.response)
            print(e.response.status_code)
            raise e

    mymessage = await update.message.reply_text("Controllo, un secondo...")

    account_id = accounts["accounts"][0]

    account = client.account_api(id=account_id)
    balances = account.get_balances()

    saldo = balances['balances'][0]['balanceAmount']['amount']
    ref_date = balances['balances'][0]['referenceDate']

    message = f'Saldo al {ref_date}: {saldo} EUR'
    await mymessage.edit_text(message)