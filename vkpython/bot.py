import vk
from config import *
from requests import *
import os

session = vk.Session(access_token = VK_API_ACCESS_TOKEN)
api = vk.API(session, v = VK_API_VERSION)

# Первый запрос к LongPoll: получаем server и key
longPoll = api.messages.getLongPollServer(lp_version = 2)
server, key, ts = longPoll['server'], longPoll['key'], longPoll['ts']

while True:
	# Последующие запросы: меняется только ts
	longPoll = post('https://%s'%server, data = {'act': 'a_check',
							    'key': key,
							    'ts': ts,
							    'wait': 25,
							    'mode': 2,
							    'version': 2}).json()
	try:
		for update in longPoll['updates']:
			if update[0] == 4 and update[2] != 515:
				api.messages.markAsRead(peer_id = update[3])
				
				name = api.users.get(user_ids = update[3])[0]['first_name']
				
				# Скачиваем файл с Яндекс.SpeechKit и загружаем на сервера ВК
				with open('audio.mp3', 'wb') as out_stream:
					req = get('https://tts.voicetech.yandex.net/generate?text=Привет, %s!&format=mp3&lang=ru-RU&speaker=jane&emotion=good&key=%s'%(name,YANDEX_API_KEY), stream=True)
					for chunk in req.iter_content(1024):
						out_stream.write(chunk)
				afile = post(api.docs.getMessagesUploadServer(type = 'audio_message', peer_id = update[3])['upload_url'], files = {'file': open('audio.mp3', 'rb')}).json()['file']
				doc = api.docs.save(file = afile, title = 'Voice message')[0]
				owner, docid = doc['owner_id'], doc['id']
				
				
				# Загружаем картинку на сервера ВК
				pfile = post(api.photos.getMessagesUploadServer(peer_id = update[3])['upload_url'], files = {'photo': open('python.jpeg', 'rb')}).json()
				photo = api.photos.saveMessagesPhoto(server = pfile['server'], photo = pfile['photo'], hash = pfile['hash'])[0]
				photoid = photo['id']
				
				# Отправляем сообщение "Привет, <first_name>!" с аудиосообщением из Яндекс.SpeechKit и картинкой
				api.messages.send(peer_id = update[3], message = 'Привет, %s &#128521;'%name, attachment = 'doc%s_%s,photo%s_%s'%(owner, docid, owner, photoid))
				
				# Удаляем файл Яндекс.SpeechKit
				os.remove(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'audio.mp3'))
	
	# Если по какой-то причине updates не найдено
	except KeyError:
		pass
	# Меняется ts для следующего запроса
	ts = longPoll['ts']
	
