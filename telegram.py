import time, requests, re
from fuzzywuzzy import fuzz
from telethon.sync import TelegramClient
from telethon import events

tmdat = time.strftime("%Y-%m-%d %H:%M")
#api ID
TG_API_ID = '40****75'
#api hash
TG_API_HASH = '71660bb3*********92ed9a98e'
#Имя пользователя tg
TG_USERNAME = 't******2'

api_id = TG_API_ID
api_hash = TG_API_HASH
username = TG_USERNAME
client = TelegramClient(username, api_id, api_hash)
#Канал с подгруппами принимающий сообщения
flood = 1234567
#Каналы за которыми НЕ следить
bad_channel = [1234, 56789, flood]

#тут будем хранить последние посты чтобы не дублироваться
old_news = []

def clean_text(stroka):
    stroka = re.sub(r'[^\w\s]', '', str(stroka))
    stroka = re.sub(r'\s+', ' ', stroka)
    stroka = stroka.lower()
    return stroka
def GetInteres(text):
    txt = clean_text(text)
    new_words = []
    for word in txt.split():
        if len(word) >= 4:
            new_words.append(word)
    in_words = len(new_words)
    interes = 0
    otvet = 0
    #тригеры, встретив эти слова в тексте агримся на пост
    triggers = ['слово','слово2','город']
    #разбираем сообщение на окраску
    mvd = ['умвд','генерал','увд']
    hot = ['взрыв','взорвался','хлопок','ликвидировали','пожар','горит','горят','загорелся']
    dtp = ['дтп ','сбил ','водитель','авария','автоледи']
    svo = ['беспилотник','пво ','ракета','дрг ','бпла ','обстреляли','атаковали','вiбух']
    #в зависимости от окраски делаем репост, в моем случае идет репост на определенные сообщения (это фишка для
    # обсуждений с вложенными категориями, нововведение от ТГ, когда в одном канале, множество папок, которые
    # представляют собой обычные посты, и чтобы написать в нужной категории нужно просто репостить нужный пост
    colors = {'4':0,'6':0,'2':0,'75':0,'27':0}

    #тут все примитивно и без красоты, пробигаемся по каждому направлению строк
    for i in range(0, in_words):
        for q in range(0, len(triggers)):
            sravnenie = fuzz.WRatio(triggers[q], new_words[i])
            if sravnenie >= 90:
                interes += 1
                colors['4'] += 1
        for q in range(0, len(svo)):
            sravnenie = fuzz.WRatio(svo[q], new_words[i])
            if sravnenie >= 90:
                colors['6'] += 1
        for q in range(0, len(mvd)):
            sravnenie = fuzz.WRatio(mvd[q], new_words[i])
            if sravnenie >= 90:
                colors['2'] += 1
        for q in range(0, len(dtp)):
            sravnenie = fuzz.WRatio(dtp[q], new_words[i])
            if sravnenie >= 90:
                colors['75'] += 1
        for q in range(0, len(hot)):
            sravnenie = fuzz.WRatio(hot[q], new_words[i])
            if sravnenie >= 90:
                colors['27'] += 1
        otvet = round(interes / in_words * 100, 2)
    return otvet,interes,colors

#проверяем пост на дублирование
def doubler(text):
    text = text[:150]
    oldest = 0
    ln = len(old_news)
    for q in range(0, ln-1, 1):
        dbl = fuzz.WRatio(old_news[q], text)
        if dbl > 86:
            oldest += 1
            break
    if oldest == 0:
        old_news.append(text)
    #запоминаем последнии 100 постов и с ними сравниваем
    if ln > 100:
        print(f"Array news full [{ln}] cleaned!")
        old_news.clear()
    return oldest, ln

@client.on(events.NewMessage())
async def normal_handler(event):
    try:
        telegram = event.message.to_dict()
        message = telegram['message']
        if message != '':
            post_id = telegram['id']
            if telegram['peer_id']['_'] == 'PeerChannel':
                channel_id = telegram['peer_id']['channel_id']
            elif telegram['peer_id']['_'] == 'PeerUser':
                channel_id = telegram['peer_id']['user_id']
            if channel_id in bad_channel:
                print(f"BadChannel {channel_id}")
            else:
                chat_from = event.chat if event.chat else (await event.get_chat())
                chat_t = chat_from.to_dict()
                chat_title = chat_t['username']
                o,i,c = GetInteres(message)
                if i > 0:
                    d, dcounter = doubler(message)
                    if d == 0:
                        if chat_title is not None:
                            url = "https://t.me/" + str(chat_title) + "/" + str(post_id)
                            returned_text = str(message)+" \n Источник: "+str(url)
                            for key, value in c.items():
                                if value > 0:
                                    await client.send_message(flood, returned_text, reply_to=int(key))
                        else:
                            url = "https://t.me/c/" + str(channel_id) + "/" + str(post_id)
                            returned_text = str(message)+" \n Источник: "+str(url)
                            for key, value in c.items():
                                if value > 0:
                                    await client.send_message(flood, returned_text, reply_to=int(key))
    except TypeError as err:
        print(f'Type ERROR: {err}')
    except KeyError as ker:
        print(f'Error user_id: {ker}')
    except ValueError as ver:
        print(f'{ver} ({tmdat})')
    except ConnectionError as err2:
        print(f'{err2} ({tmdat})')
    except requests.exceptions.ConnectionError as err3:
        print(err3)
    except:
        print('Except error \n')
try:
    client.start()
    client.run_until_disconnected()
except ConnectionError as err2:
    print(err2)