import os
from random import randint
from requests import *
import vk

# Указываем ключи доступа, id группы и версию API
YANDEX_API_KEY = '***'
VK_API_ACCESS_TOKEN = '***'
VK_API_VERSION = '5.95'
GROUP_ID = 123


session = vk.Session(access_token = VK_API_ACCESS_TOKEN)
api = vk.API(session, v = VK_API_VERSION)

# Первый запрос к LongPoll: получаем server и key
longPoll = api.groups.getLongPollServer(group_id = GROUP_ID)
server, key, ts = longPoll['server'], longPoll['key'], longPoll['ts']

while True:
    # Последующие запросы: меняется только ts
    longPoll = post('%s'%server, data = {'act': 'a_check',
                                         'key': key,
                                         'ts': ts,
                                         'wait': 25}).json()


    if longPoll['updates'] and len(longPoll['updates']) != 0:
        for update in longPoll['updates']:
            if update['type'] == 'message_new':
                print(update)
                # Помечаем сообщение от этого пользователя как прочитанное
                api.messages.markAsRead(peer_id = update['object']['from_id'])

                # Запрашиваем имя пользователя
                name = api.users.get(user_ids = update['object']['from_id'])[0]['first_name']

                # Скачиваем аудиофайл "Привет, %name%" с Яндекс.SpeechKit и загружаем на сервера ВК
                with open('audio.mp3', 'wb') as out_stream:
                    req = get('https://tts.voicetech.yandex.net/generate?text=Привет, %s!&format=opus&lang=ru-RU&speaker=jane&emotion=good&key=%s'%(name, YANDEX_API_KEY), stream = True)
                    for chunk in req.iter_content(1024):
                        out_stream.write(chunk)
                afile = post(api.docs.getMessagesUploadServer(type = 'audio_message', peer_id = update['object']['from_id'])['upload_url'], files = {'file': open('audio.mp3', 'rb')}).json()['file']
                doc = api.docs.save(file = afile, title = 'Voice message')['audio_message']
                print(doc)

                # Загружаем картинку на сервера ВК
                pfile = post(api.photos.getMessagesUploadServer(peer_id = update['object']['from_id'])['upload_url'], files = {'photo': open('python.jpeg', 'rb')}).json()
                photo = api.photos.saveMessagesPhoto(server = pfile['server'], photo = pfile['photo'], hash = pfile['hash'])[0]

                # Отправляем сообщение "Привет, %name%" с аудиосообщением из Яндекс.SpeechKit и картинкой
                api.messages.send(user_id = update['object']['from_id'], random_id = randint(-2147483648, 2147483647), message = 'Привет, %s &#128521;'%name, attachment = 'doc%s_%s,photo%s_%s'%(doc['owner_id'], doc['id'], doc['owner_id'], photo['id']))

                # Удаляем файл Яндекс.SpeechKit
                os.remove(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'audio.mp3'))


    # Меняем ts для следующего запроса
    ts = longPoll['ts']
