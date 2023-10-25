from telegram import LabeledPrice, Update
from telegram.ext import ContextTypes

import config
from utils import printlog

PAYMENT_PROVIDER_TOKEN = config.TOKEN_PAGAMENTO


async def donazioni(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends an invoice without shipping-payment."""
    chat_id = update.message.chat_id
    title = "Donazione"
    description = "Una donazione per supportare il bot e il suo creatore"
    # select a payload just for you to recognize its the donation from your bot
    payload = "ItsFromEmilyTheBot"
    # In order to get a provider_token see https://core.telegram.org/bots/payments#getting-a-token
    currency = "EUR"
    # price in dollars
    price = 5
    # price * 100 so as to include 2 decimal points
    prices = [LabeledPrice("Donazione", price * 100)]

    await context.bot.send_invoice(
        chat_id,
        title,
        description,
        payload,
        PAYMENT_PROVIDER_TOKEN,
        currency,
        prices,
        max_tip_amount=9900,
        suggested_tip_amounts=[300, 800, 1800, 9700],
    )


# after (optional) shipping, it's the pre-checkout
async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Answers the PreQecheckoutQuery"""
    query = update.pre_checkout_query

    # check the payload, is this from your bot?
    if query.invoice_payload != "ItsFromEmilyTheBot":
        await query.answer(ok=False, error_message="Qualcosa è andato storto...")
    else:
        await query.answer(ok=True)


# finally, after contacting the payment provider...
async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Confirms the successful payment."""
    # do something after successfully receiving payment?
    await printlog(update, "ha donato qualcosa.")
    await update.message.reply_text("Grazie! Pagamento effettuato!")
