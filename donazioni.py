    # application.add_handler(CommandHandler("noshipping", start_without_shipping_callback))

    # # Optional handler if your product requires shipping
    # application.add_handler(ShippingQueryHandler(shipping_callback))

    # # Pre-checkout handler to final check
    # application.add_handler(PreCheckoutQueryHandler(precheckout_callback))

    # # Success! Notify your user!
    # application.add_handler(
    #     MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback)
    # )


from telegram import LabeledPrice, ShippingOption, Update
import config
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    PreCheckoutQueryHandler,
    ShippingQueryHandler,
    filters,
)
from utils import printlog, get_display_name, get_now, get_chat_name, no_can_do

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
    price = 2
    # price * 100 so as to include 2 decimal points
    prices = [LabeledPrice("Donazione", price * 100)]

    # optionally pass need_name=True, need_phone_number=True,
    # need_email=True, need_shipping_address=True, is_flexible=True

    await context.bot.send_invoice(chat_id, title, description, payload, PAYMENT_PROVIDER_TOKEN, currency, prices, max_tip_amount=9900, suggested_tip_amounts=[300, 800, 1800, 9700])


# async def shipping_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     """Answers the ShippingQuery with ShippingOptions"""
#     query = update.shipping_query
#     # check the payload, is this from your bot?
#     if query.invoice_payload != "ItsFromEmilyTheBot":
#         # answer False pre_checkout_query
#         await query.answer(ok=False, error_message="Qualcosa è andato storto...")
#         return

#     # First option has a single LabeledPrice
#     options = [ShippingOption("1", "Shipping Option A", [LabeledPrice("A", 100)])]
#     # second option has an array of LabeledPrice objects
#     price_list = [LabeledPrice("B1", 150), LabeledPrice("B2", 200)]
#     options.append(ShippingOption("2", "Shipping Option B", price_list))
#     await query.answer(ok=True, shipping_options=options)


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