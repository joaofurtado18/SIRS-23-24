import json
import os
import requests
import io
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import json
import sys
import base64
from cryptography.hazmat.primitives.ciphers import Cipher , algorithms , modes
from cryptography.hazmat.backends import default_backend

import os
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, '../../')
from safe_sound import SafeSound

safe_sound = SafeSound()


class KeyManager:
	def __init__(self):
		self.private_key = None
		self.public_key = None
		if len(sys.argv) > 1:
			self.load_fk_from_file(f'../keys/{sys.argv[1]}')
		elif os.path.isfile('keys/family_key.pem'):
			self.load_fk_from_file('keys/family_key.pem')
		else:
			print("Family key not found. Please provide the path to a family key file")

	def generate_key_pair(self):
		private_key = rsa.generate_private_key(
			public_exponent=65537,
			key_size=2048
		)
		public_key = private_key.public_key()

		self.private_key = private_key
		self.public_key = public_key

		return private_key, public_key
	

	def save_fk_to_file(self, key, filename='keys/family_key.pem'):
		with open(filename, 'wb') as key_file:
			key_file.write(key)
		self.family_key = key


	def load_fk_from_file(self, filename='keys/family_key.pem'):
		with open(filename, 'rb') as key_file:
			self.family_key = key_file.read()
		return self.family_key
	

	def save_pair_to_files(self, private_key_filename='keys/private_key.pem', public_key_filename='keys/public_key.pem'):
		with open(private_key_filename, 'wb') as private_key_file:
			private_key_bytes = self.private_key.private_bytes(
				encoding=serialization.Encoding.PEM,
				format=serialization.PrivateFormat.PKCS8,
				encryption_algorithm=serialization.NoEncryption()
			)
			private_key_file.write(private_key_bytes)

		with open(public_key_filename, 'wb') as public_key_file:
			public_key_bytes = self.public_key.public_bytes(
				encoding=serialization.Encoding.PEM,
				format=serialization.PublicFormat.SubjectPublicKeyInfo
			)
			public_key_file.write(public_key_bytes)


class Client:
	def __init__(self, host, port, certificate):
		self.url = f'https://{host}:{port}'
		self.cert = certificate
		self.key_manager = KeyManager()
		self.jwt = None

      
	def register(self, username, password):
		_, public_key = self.key_manager.generate_key_pair()
		self.key_manager.save_pair_to_files()

		public_key_pem = public_key.public_bytes(
			encoding=serialization.Encoding.PEM,
			format=serialization.PublicFormat.SubjectPublicKeyInfo
		)

		encrypted_public_key = SafeSound.encrypt_public_key(self.key_manager.family_key, public_key_pem)
		encrypted_public_key_b64 = base64.b64encode(encrypted_public_key).decode('utf-8')
		
		response = requests.post(f'{self.url}/register', json={
			'username': username,
			'password': password,
			'public_key': encrypted_public_key_b64
		},
		verify=self.cert)

		if not response.status_code == 201:
			print(json.dumps(response.json(), indent=2))
			return

		print("Sending public key to server...", public_key_pem.decode('utf-8'))


	def login(self, username, password):
		response = requests.post(f'{self.url}/login', json={
			'username': username,
			'password': password
		},
		verify=self.cert)
		if not response.status_code == 200:
			print(json.dumps(response.json(), indent=2))
			return
		self.jwt = response.json()['access_token']
		print(json.dumps(response.json()['message'], indent=2))


	def catalog(self):
		response = requests.get(f'{self.url}/catalog', verify=self.cert)
		print()
		print(json.dumps(response.json(), indent=2))
  

	def buy(self, id):
		if self.jwt is None:
			print("You must be logged in to buy media.")
			return
		response = requests.put(f'{self.url}/{id}/buy', headers={
		'Authorization': f'Bearer {self.jwt}'
		},
		verify=self.cert)
		print(json.dumps(response.json(), indent=2))


	def library(self):
		if self.jwt is None:
			print("You must be logged in to view your library.")
			return
		response = requests.get(f'{self.url}/library', headers={
		'Authorization': f'Bearer {self.jwt}'
		},
		verify=self.cert)
		print(json.dumps(response.json(), indent=2))
			

	def get_media(self, id):
		if self.jwt is None:
			print("You must be logged in to get media.")
			return
		response = requests.get(
			f'{self.url}/get_media/{id}',
			headers={'Authorization': f'Bearer {self.jwt}'},
			verify=self.cert
		)
		if not response.status_code == 200:
			print(json.dumps(response.json(), indent=2))
			return
		
		content_pieces = response.text.split('\n')
		json_chunk = json.loads(content_pieces[0])

		encrypted_key = json_chunk['key']
		encrypted_key_bytes = base64.b64decode(encrypted_key.encode('utf-8'))
		iv = encrypted_key_bytes[:16]
		ciphertext = encrypted_key_bytes[16:]
		cipher = Cipher(algorithms.AES(self.key_manager.family_key), modes.CFB(iv), backend=default_backend())
		decryptor = cipher.decryptor()
		decrypted_key = decryptor.update(ciphertext) + decryptor.finalize()

		audio_data = content_pieces[1]
		print("AUDIO DATA: ", audio_data)
		protected_json = json_chunk['media']
		protected_json['media']['mediaContent']['encrypted_audioBase64'] = audio_data

		safe_sound.write_json("media.json", protected_json)
		safe_sound.check("media.json", decrypted_key)
		safe_sound.unprotect("media.json", "media_unprotected.json", decrypted_key)
		media = safe_sound.read_json("media_unprotected.json")
		print(json.dumps(media, indent=2))

	
	
	def delete_media(self, id):
		if self.jwt is None:
			print("You must be logged in to delete media.")
			return
		reponse = requests.delete(f'{self.url}/delete_media/{id}', headers={
		'Authorization': f'Bearer {self.jwt}'
		},
		verify=False)
		print(json.dumps(reponse.json(), indent=2))
	

	def update_media(self, current_title, new_title):
			if self.jwt is None:
				print("You must be logged in to update media.")
				return
			response = requests.post(
				f'{self.url}/update_media/{current_title}/{new_title}',
				headers={'Authorization': f'Bearer {self.jwt}'},
				data={'current_title': current_title, 'new_title': new_title},
				verify=False
			)
			print(json.dumps(response.json(), indent=2))


	def create_media(self):
		if self.jwt is None:
			print("You must be logged in to create media.")
			return
		response = requests.post(
		f'{self.url}/create_media',
		headers={'Authorization': f'Bearer {self.jwt}'},
		verify=False
		)
		print(json.dumps(response.json(), indent=2))

	def users(self):
		if self.jwt is None:
			print("You must be logged in to view users.")
			return
		response = requests.get(f'{self.url}/users', headers={
		'Authorization': f'Bearer {self.jwt}'
		},
		verify=self.cert)
		print(json.dumps(response.json(), indent=2))


	def families(self):
		if self.jwt is None:	
			print("You must be logged in to view families.")
			return
		response = requests.get(f'{self.url}/families', headers={
		'Authorization': f'Bearer {self.jwt}'
		},
		verify=self.cert)
		print(json.dumps(response.json(), indent=2))


	def join_family(self, id):
		if self.jwt is None:
			print("You must be logged in to join a family.")
			return
		response = requests.put(f'{self.url}/family/{id}/join', headers={
		'Authorization': f'Bearer {self.jwt}'
		},
		verify=self.cert)
		if not response.status_code == 200:
			print(json.dumps(response.json(), indent=2))
			return
		encrypted_fk_text = response.json()['fk']
		encrypted_fk_bytes = base64.b64decode(encrypted_fk_text.encode('utf-8'))
		fk_bytes = SafeSound.decrypt_secret_key(self.key_manager.private_key, encrypted_fk_bytes)
		self.key_manager.save_fk_to_file(fk_bytes)
		self.key_manager.load_fk_from_file()
		print(json.dumps(response.json(), indent=2))


if __name__ == '__main__':
	certificate = "../../certificates/cert.pem"
	cwd = os.getcwd()
	certificate = os.path.join(cwd, certificate)

	client = Client(os.getenv("SERVER_HOST"), os.getenv("SERVER_PORT"), certificate)

	while True:
		print('''
	reg: Register
	log: Login
	cat: View the Catalog
	buy: Buy Media
	lib: View your Library
	med: Access Media
	get: Get Media
	del: Delete Media
	upd: Update Media
	cre: Create Media
	usr: View Users
	fam: View Families
	jfam: Join Family
	quit: q
		''')

		choice = input('Enter choice: ')

		if choice == 'reg':
			username = input('username: ')
			password = input('password: ')
			client.register(username, password)

		elif choice == 'log':
			username = input('username: ')
			password = input('password: ')
			client.login(username, password)

		elif choice == 'cat':
			client.catalog()

		elif choice == 'buy':
			id = input('media id: ')
			client.buy(id)

		elif choice == 'lib':
			client.library()
		
		elif choice == 'get':
			id = input('media id: ')
			client.get_media(id)
		
		elif choice == 'del':
			id = input('media id: ')
			client.delete_media(id)

		elif choice == 'upd':
			current_title = input('current title: ')
			new_title = input('new title: ')
			client.update_media(current_title, new_title)
		
		elif choice == 'cre':
			client.create_media()

		elif choice == 'usr':
			client.users()

		elif choice == 'fam':
			client.families()

		elif choice == 'jfam':
			id = input('family id: ')
			client.join_family(id)

		elif choice == 'q':
			break
		else:
			print('Invalid choice')
		print()
		input('Press Enter to continue...')
