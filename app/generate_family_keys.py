import os


if __name__ == '__main__':
  key = os.urandom(16)
  with open('key.pem', 'wb') as key_file:
    key_file.write(key)