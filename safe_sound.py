import json
from cryptography.hazmat.primitives import hashes, hmac, padding, asymmetric, serialization
from cryptography.hazmat.primitives.ciphers import Cipher , algorithms , modes
from cryptography.hazmat.backends import default_backend
import base64
import datetime
import os
import argparse
import secrets


class SafeSound:
	def __init__(self):
		self.random_numbers_map = {}
		self.map_filename = 'random_numbers_map.json'
		self.load_map()


	def load_map(self):
		if os.path.exists(self.map_filename):
			with open(self.map_filename, 'r') as f:
				self.random_numbers_map = json.load(f)


	def save_map(self):
		with open(self.map_filename, 'w') as f:
			json.dump(self.random_numbers_map, f)


	def help(self):
		print("Available commands:")
		print("\t python3 safe_sound protect <input_file> <output_file> - encrypts the input file and saves it to the output file")
		print("\t python3 safe_sound unprotect <input_file> <output_file> - decrypts the input file and saves it to the output file")
		print("\t python3 safe_sound check <input_file> - checks the integrity of the input file")

	
	def run_command(self, args):
		if args.command == 'help':
			self.help()

		elif args.command == 'protect':
			if len(args.arguments) != 2:
				print("Error: 'protect' command requires two arguments - input-file and output-file.")
			else:
				self.protect(args.arguments[0], args.arguments[1])
				print(f"Document protected and saved to {args.arguments[1]}")

		elif args.command == 'unprotect':
			if len(args.arguments) != 2:
				print("Error: 'unprotect' command requires two arguments - input-file and output-file.")
			else:
				self.unprotect(args.arguments[0], args.arguments[1])
				print(f"Document unprotected and saved to {args.arguments[1]}")

		elif args.command == 'check':
			if len(args.arguments) != 1:
				print("Error: 'check' command requires one argument - input-file.")
			else:
				result = self.check(args.arguments[0])
				if result:
					print("Document integrity verified.")
				else:
					print("Document integrity check failed.")
		else:
			print(f"Error: Unknown command '{args.command}'. Use 'help' for available commands.")


	def read_json(self, filename: str) -> dict:
		with open(filename) as f:
			data = json.load(f)
		return data
	
	
	def write_json(self, filename, data):
		with open(filename, 'w') as f:
			json.dump(data, f, indent=2)


	def read_key(self, filename: str) -> bytes:
		key_path = os.path.abspath(os.path.join(os.path.dirname(__file__), filename))
		with open(key_path, 'rb') as f:
			key = f.read()
		return key
	
	
	def calculate_hash(self, key: bytes, data: dict) -> bytes:
		document_bytes = json.dumps(data, sort_keys=True).encode()
		h = hmac.HMAC(key, hashes.SHA256(), backend=default_backend())
		h.update(document_bytes)
		return h.finalize()
	
	
	def generate_random_number(self):
		return secrets.randbelow(1000000)
	

	def protect(self, filename, output_filename, key):
		data = self.read_json(filename)
		audio_base64 = data['media']['mediaContent'].pop('audioBase64', None)

		iv = os.urandom(16)

		padder = padding.PKCS7(algorithms.AES.block_size).padder()
		padded_data = padder.update(audio_base64.encode('utf-8')) + padder.finalize()
		cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())
		encryptor = cipher.encryptor()
		ciphertext = encryptor.update(padded_data) + encryptor.finalize()
		encrypted_audio_base64 = base64.b64encode(iv + ciphertext).decode('utf-8')

		timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

		random_number = self.generate_random_number()

		encrypted_dict = data
		encrypted_dict['timestamp'] = timestamp
		encrypted_dict['random_number'] = random_number
		encrypted_dict['media']['mediaContent']['encrypted_audioBase64'] = encrypted_audio_base64

		hash_bytes = self.calculate_hash(key, encrypted_dict)
		encrypted_dict['hash'] = base64.b64encode(hash_bytes).decode()

		self.write_json(output_filename, encrypted_dict)


	def unprotect(self, filename, output_filename, key):
		data = self.read_json(filename)

		encrypted_data = base64.b64decode(data['media']['mediaContent']['encrypted_audioBase64'])
		iv = encrypted_data[:16]  # IV is the first 16 bytes
		ciphertext = encrypted_data[16:]

		cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())
		decryptor = cipher.decryptor()
		decrypted_data = decryptor.update(ciphertext) + decryptor.finalize()

		unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
		unpadded_data = unpadder.update(decrypted_data) + unpadder.finalize()

		decrypted_dict = data
		decrypted_dict['media']['mediaContent']['audioBase64'] = unpadded_data.decode('utf-8')
		decrypted_dict['media']['mediaContent'].pop('encrypted_audioBase64', None)
		decrypted_dict.pop('timestamp', None)
		decrypted_dict.pop('random_number', None)
		decrypted_dict.pop('hash', None)
		self.write_json(output_filename, decrypted_dict)


	def check(self, filename, key) -> bool:
		data = self.read_json(filename)

		if 'hash' not in data or 'timestamp' not in data or 'random_number' not in data:
			return False

		json_timestamp = data['timestamp']
		json_timestamp_datetime = datetime.datetime.strptime(json_timestamp, '%Y-%m-%d %H:%M:%S')
		current_timestamp = datetime.datetime.now()
		time_difference = current_timestamp - json_timestamp_datetime
		acceptable_time_difference = datetime.timedelta(seconds=5)

		if time_difference <= acceptable_time_difference:
			print("Timestamp acceptable. Checking hash and random number...")

			# Check if the random number for the timestamp is unique
			if self.is_random_number_unique(json_timestamp, data['random_number']):
				data_without_hash = {key: value for key, value in data.items() if key not in ['hash']}
				new_hash_bytes = self.calculate_hash(key, data_without_hash)

				print("Hashes match:", base64.b64encode(new_hash_bytes).decode() == data['hash'])
				return base64.b64encode(new_hash_bytes).decode() == data['hash']
			else:
				print("Random number is not unique for the timestamp.")
				return False
		else:
			print("Timestamp not acceptable. Rejecting.")
			return False
		

	def is_random_number_unique(self, timestamp, random_number):
		# Check if the random number is unique for the given timestamp
		if timestamp not in self.random_numbers_map:
			self.random_numbers_map[timestamp] = random_number
			return True
		return self.random_numbers_map[timestamp] != random_number
	
	
	def create_and_protect(self, new_media):
		json_data = {
			"media": {
				"mediaInfo": {
					"owner": "Bob",
					"format": new_media.format,
					"artist": new_media.artist,
					"title": new_media.title,
					"genre": new_media.genre
				},
				"mediaContent": {
					"lyrics": new_media.lyrics,
					"audioBase64": new_media.audio_base64
				}
			}
		}
		
		self.write_json('new_media', json_data)
		self.protect('new_media', 'protected_media.json')
	
	
	# generates a random 256 bit secret key
	def generate_secret_key():
		return os.urandom(32)

	def encrypt_secret_key(client_public_key, secret_key):

		public_key = serialization.load_pem_public_key(
			client_public_key,
			backend=default_backend()
		)

		encrypted_key = public_key.encrypt(
			secret_key,
			asymmetric.padding.OAEP(
				mgf=asymmetric.padding.MGF1(algorithm=hashes.SHA256()),
				algorithm=hashes.SHA256(),
				label=None
			)
		)

		return encrypted_key
	
	
	def decrypt_secret_key(client_private_key, encrypted_key):
		private_key = client_private_key

		decrypted_key = private_key.decrypt(
			encrypted_key,
			asymmetric.padding.OAEP(
				mgf=asymmetric.padding.MGF1(algorithm=hashes.SHA256()),
				algorithm=hashes.SHA256(),
				label=None
			)
		)

		return decrypted_key
	

	def encrypt_public_key(secret_key, public_key):
		iv = os.urandom(16)
		cipher = Cipher(algorithms.AES(secret_key), modes.CFB(iv), backend=default_backend())
		encryptor = cipher.encryptor()
		encrypted_public_key = encryptor.update(public_key) + encryptor.finalize()
		
		return iv + encrypted_public_key
	

	def decrypt_public_key(secret_key, encrypted_public_key):
		iv = encrypted_public_key[:16]
		ciphertext = encrypted_public_key[16:]
		cipher = Cipher(algorithms.AES(secret_key), modes.CFB(iv), backend=default_backend())
		decryptor = cipher.decryptor()
		decrypted_public_key = decryptor.update(ciphertext) + decryptor.finalize()

		return decrypted_public_key
	

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Cryptographic operations on a document.')
	parser.add_argument('command', choices=['protect', 'unprotect', 'check', 'help'], help='Command to perform')
	parser.add_argument('arguments', nargs='*', help='Command arguments')

	args = parser.parse_args()

	safe_sound = SafeSound()

	try:
		safe_sound.run_command(args)
	finally:
		safe_sound.save_map()