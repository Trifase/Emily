import asyncio
import json

from telegram.ext import PicklePersistence


def dump_json_custom(data, file_name):
    filename = f"{file_name}.json"
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)


file = "db/picklepersistence"


def pickle_persistence():
    return PicklePersistence(
        filepath="db/picklepersistence",
        single_file=True,
        on_flush=False,
    )

PROCESS_CHAT_DATA = False
PROCESS_USER_DATA = False

REMOVE_EMPTY_KEYS = False
REMOVE_EMPTY_SUBKEYS = False
REMOVE_SPECIFIC_KEYS = False

SAVE = False


async def main():
    chat_data = await pickle_persistence().get_chat_data()
    bot_data = await pickle_persistence().get_bot_data()
    user_data = await pickle_persistence().get_user_data()
    
    #save each data in a json file:
    dump_json_custom(chat_data, "persistence_chat_data.json")
    dump_json_custom(bot_data, "persistence_bot_data.json")
    dump_json_custom(user_data, "persistence_user_data.json")

    # for key, value in user_data.items():
    #     print(key, value)

        #         print(f'user_data[{user}] = {user_value}')
            # this_user_value = user_value
            # print(this_user_id, this_user_data)


            # if this_user_data:
            #     if this_user_data.get('default_meteo_city'):
            #         if this_user_data.get('user_settings'):
            #             this_user_data['user_settings']['prometeo_city'] = this_user_data['default_meteo_city']
            #             # this_user_data.pop('default_meteo_city', None)
            #             print(f"Aggiunto prometeo_city a {this_user_id}")
            #         else:
            #             this_user_data['user_settings'] = {'prometeo_city': this_user_data['default_meteo_city']}
            #             # this_user_data.pop('default_meteo_city', None)
            #             print(f"Aggiunto prometeo_city a {this_user_id}")

            # remove empty keys
        #     if REMOVE_EMPTY_KEYS:
        #         if not user_value:
        #             n += 1
        #             await pickle_persistence().drop_user_data(this_user_id)

        #     # remove empty subkeys
        #     if REMOVE_EMPTY_SUBKEYS:
        #         for u_subkey, u_subvalue in list(this_user_value.items()):
        #             if not u_subvalue:
        #                 this_user_data.pop(u_subkey, None)

        #     # remove chat_data_remove
        #     if REMOVE_SPECIFIC_KEYS:
        #         for u_k in user_data_remove:
        #             this_user_data.pop(u_k, None)

        #     if SAVE:
        #         await pickle_persistence().update_user_data(user_id=this_user_id, data=this_user_data)
        # print(n)

    # await pickle_persistence().update_bot_data(bot_data)


asyncio.run(main())


# lotto_history = bot_data['lotto_history']


# lista = []
# for datapoint in lotto_history:
#     ora = datapoint[:16].split("_")
#     numero = datapoint[-5:]
#     lista.append([ora[0], ora[1], numero])
# # print(lista)

# import xlsxwriter


# with xlsxwriter.Workbook('test.xlsx') as workbook:
#     worksheet = workbook.add_worksheet()

#     for row_num, data in enumerate(lista):
#         worksheet.write_row(row_num, 0, data)

# print(bot_data)

# ### CLEANUP ###
# a = 0
# b = 0
# c = 0
# bot_data_to_remove = ['tentativi_indovina', 'indovina_stats']
# for key in bot_data_to_remove:
#     a += 1
#     mydict["bot_data"].pop(key, None)

# # /getchat -1001329447461 Nome: #diochan
# # /getchat -1001146498129 Nome: Lotto Ucraina
# # /getchat -1001171934343 Nome: r/🇺🇦❤️🇷🇺 - Dalla parte di Putin ma solidarietà al popolo ucraino
# # /getchat -1001255745056 Nome: Asphalto: Alta Direzione
# # /getchat -1001180175690 Nome: Bot Testing
# # /getchat -1001055180693 Nome: R****t Italy Group - saluti
# # /getchat -1001470497979 Nome: Gran Casinò Ludopatia
# # /getchat -1001377760263 Nome: Natale in India

# for k in list(mydict["chat_data"]):
#     if mydict["chat_data"][k]:
#         pass
#     else:
#         b += 1
#         mydict["chat_data"].pop(k, None)

# chat_data_to_pop = [-1001329447461, -1001146498129, -1001171934343, -1001255745056, -1001180175690, -1001055180693, -1001377760263]
# for i in chat_data_to_pop:
#     b += 1
#     mydict["chat_data"].pop(i, None)

# mydict["chat_data"][-1001470497979].pop("2021-09-29", None)
# mydict["chat_data"].pop("highest_wins", None)
# b += 2


# for k in list(mydict["user_data"]):
#     if mydict["user_data"][k]:
#         if mydict["user_data"][k]["balance"] == 0 and mydict["user_data"][k]["banca"] == 0:
#             c += 1
#             mydict["user_data"].pop(k, None)
#         else:
#             pass
#     else:
#         c += 1
#         mydict["user_data"].pop(k, None)

# print(f"{a} keys removed from bot_data")
# print(f"{b} keys removed from chat_data")
# print(f"{c} keys removed from user_data")

# ### FINE CLEANUP ###


# file = "db/picklepersistence"
# with open(file, 'rb') as pickle_file:
#     mydict = pickle.load(pickle_file)


# print(mydict)


# print(mydict)


# ddf = 14770193
# aurora = 208435168
# casino = -1001470497979
# santa = -1001377760263

# mydict["bot_data"]["scommesse_emily"] = []
# print(mydict["chat_data"][santa])


# mydict["chat_data"][santa]['santa2021']

# print(mydict["chat_data"][santa]['santa2021'])
# for nickname, value in mydict["chat_data"][santa]['santa2021'].items():
#     data = mydict["chat_data"][santa]['santa2021'][nickname]
#     data[2] = False
# print(mydict["chat_data"][santa]['santa2021'])
# for k,v in mydict["chat_data"][santa]['santa2021'].items():
#     if str(k).startswith("@"):
#         if len(v[0]) == 0:
#             mydict["chat_data"][santa]['santa2021'].pop(k, None)
#             print(f"Cancellato {k} perché lista vuota")
#     else:
#         mydict["chat_data"][santa]['santa2021'].pop(k, None)
#         print(f"Cancellato {k} perché senza @")


# mydict["chat_data"][santa]['santa2021'].pop('ilmionicktelegram')
# print(mydict["chat_data"][santa])
# print(mydict["user_data"][aurora])
# print(mydict)
# mydict["chat_data"][-1001470497979]['2021-09-30'] = mydict["chat_data"][-1001470497979]['2021-09-29']
# mydict["bot_data"]["tentativi_indovina"] = []
# print(mydict["bot_data"]["tentativi_indovina"])
#
# mydict["bot_data"]["cavalli_esistenti"].sort(key=operator.itemgetter('name'))

# print(cavalli_esistenti)
# for n in range(len(cavalli_esistenti)):
#     print(n, cavalli_esistenti[n])

# mydict["bot_data"]["cavalli_esistenti"][9]['emoji'] = "🤴"
# mydict["bot_data"]["cavalli_esistenti"][11]['emoji'] = "🧕"
# mydict["bot_data"]["cavalli_esistenti"][12]['emoji'] = "🛂"
# mydict["bot_data"]["cavalli_esistenti"][29]['name'] = "Arko"
# cavalli_esistenti[-2]['generazione'] = 3
# mydict["bot_data"]["cavalli_esistenti"][14]['emoji'] = "🕋"
# print(cavalli_esistenti)
# cavalli_esistenti[-5]['emoji'] = "🦠"
# cavalli_esistenti[8]['name'] = "CuoreNero"
# for cavallo in cavalli_esistenti:
# print(cavallo['corse_vinte'])
# mydata += f"{json.dumps(cavalli_esistenti)}\n"
# indovina_stats = mydict["bot_data"]["indovina_stats"]
# print(indovina_stats)
# new_stats = {}

# for i in range(1, 100):
#     new_stats[i] = 0

# for k,v in indovina_stats.items():
#     k = int(k)
#     v = int(v)
#     new_stats[k] += v
# print(mydict["bot_data"]["scommesse_ippodromo"])
# print(mydict["bot_data"]["odds_list"])
# # print(new_stats)
# indovina_stats = new_stats

# mydict["bot_data"]["cavalli_esistenti"] = cavalli_esistenti
# mydict["bot_data"]["indovina_stats"] = indovina_stats
# print(mydict["bot_data"]["gara_in_corso"])
# print(mydict["bot_data"]["scommesse_aperte"])
# print(mydict["bot_data"])
# mydict["bot_data"]["scommesse_ippodromo"] = []
# mydict["bot_data"]["odds_list"]


# # Scrittura Finale
# file_to_write = open(file, "wb")
# pickle.dump(mydict, file_to_write)
