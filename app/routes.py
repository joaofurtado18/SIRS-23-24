import os
import random
import base64
import sys
import json
from flask import Blueprint, request, jsonify, Response
from models import Family, db, Media, User
from faker import Faker 
from flask import Flask, render_template, redirect, url_for
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.ciphers import Cipher , algorithms , modes
from cryptography.hazmat.backends import default_backend

sys.path.insert(0, '../')
from safe_sound import SafeSound

bp = Blueprint('main', __name__)
fake = Faker()
safe_sound = SafeSound()


family_keys = []
files = os.listdir('keys')
files.sort()
for file in files:
    with open(f'keys/{file}', 'rb') as family_key_file:
        family_keys.append(family_key_file.read())


def get_family_key():
    return family_keys.pop(0)


def media_to_json(media):
    if not media:
        return None

    owner_name = media.owner.username if media.owner else None
    media_info = {
        "owner": owner_name,
        "format": media.format,
        "artist": media.artist,
        "title": media.title,
        "genre": media.genre
    }

    media_content = {
        "lyrics": media.lyrics,
        "audioBase64": media.audio_base64
    }

    result_json = {
        "media": {
            "mediaInfo": media_info,
            "mediaContent": media_content
        }
    }
    
    safe_sound.write_json('media.json', result_json)


@bp.route('/register', methods=['POST'])
def register():    
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    encrypted_public_key_b64 = data.get('public_key')

    if not username or not password or not encrypted_public_key_b64:
        return jsonify({'message': 'Username, password, and public key required'}), 400

    user = User.query.filter_by(username=username).first()
    if user:
        print(user.public_key)
        return jsonify({'message': 'User already exists'}), 409
    
    family_key = get_family_key()
    family_key_b64 = base64.b64encode(family_key).decode('utf-8')
    family = Family(key=family_key_b64)

    encrypted_public_key = base64.b64decode(encrypted_public_key_b64)
    public_key = SafeSound.decrypt_public_key(family_key, encrypted_public_key)
    public_key = public_key.decode('utf-8')

    user = User(username=username, password=password, public_key=public_key, family=family)
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'User created successfully'}), 201


@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()

    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    if user.password == password:
        access_token = create_access_token(identity=username)
        return jsonify({
            'message': f'Logged in as {username}',
            'access_token': access_token
        }), 200
    
    return jsonify({'message': 'Wrong password'}), 401


@bp.route('/catalog', methods=['GET'])
def catalog():
    all_media = Media.query.all()

    catalog = []
    for media in all_media:
        if media.owner:
            continue
        media_display = {
            'id': media.id,
            'title': media.title,
            'artist': media.artist
        }
        catalog.append(media_display)

    return jsonify(catalog), 200


@bp.route('/<id>/buy', methods=['PUT'])
@jwt_required()
def buy(id):
    username = get_jwt_identity()

    user = User.query.filter_by(username=username).first()
    media_to_buy = Media.query.filter_by(id=id).first()

    if not media_to_buy:
        return jsonify({'message': f'Media with id {id} not found'}), 404
    
    if media_to_buy.owner:
        return jsonify({'message': f'Media with id {id} already bought'}), 400

    media_to_buy.owner = user
    db.session.commit()
    return jsonify({'message': f'Media with id {id} bought successfully'}), 200


@bp.route('/library', methods=['GET'])
@jwt_required()
def library():
    username = get_jwt_identity()
    user = User.query.filter_by(username=username).first()

    family_users = User.query.filter_by(family=user.family).all()

    family_media = []
    for family_member in family_users:
        media = Media.query.filter_by(owner=family_member).all()
        for item in media:
            media_display = {
                'id': item.id,
                'title': item.title,
                'artist': item.artist,
                'owner': family_member.username
            }
            family_media.append(media_display)

    return jsonify(family_media), 200


@bp.route('/get_media/<id>')
@jwt_required()
def get_media(id):
    username = get_jwt_identity()
    user = User.query.filter_by(username=username).first()

    if not user:
        return jsonify({'message': 'You need to be a user'}), 401
    
    media = Media.query.filter_by(id=id).first()

    if not media:
        return jsonify({'message': f'Media with id {id} not found'}), 404
    
    if not media.owner or not media.owner.family == user.family:
        return jsonify({'message': 'You do not have access to this media'}), 403

    throwaway_key = os.urandom(32)
    family_key = base64.b64decode(user.family.key.encode('utf-8'))

    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(family_key), modes.CFB(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    encrypted_throwaway_key = iv + encryptor.update(throwaway_key) + encryptor.finalize()
    encrypted_throwaway_key_b64 = base64.b64encode(encrypted_throwaway_key).decode('utf-8')

    media_to_json(media)
    safe_sound.protect('media.json', 'media_protected.json', throwaway_key)
    media_protected = safe_sound.read_json('media_protected.json')

    def generate():
        audio_base64 = media_protected['media']['mediaContent'].pop('encrypted_audioBase64', None)

        json_data = {
            'key': encrypted_throwaway_key_b64,
            'media': media_protected
        }
        json_chunk = json.dumps(json_data) + '\n'

        yield json_chunk

        audio_data = audio_base64
        print("AUDIO DATA: ", audio_data)
        chunk_size = 1024
        for i in range(0, len(audio_data), chunk_size):
            yield audio_data[i:i + chunk_size]

    return Response(generate(), content_type='application/octet-stream')


@bp.route('/delete_media/<id>', methods=['DELETE'])
@jwt_required()
def delete_media(id):
    username = get_jwt_identity()
    user = User.query.filter_by(username=username).first()

    if not user:
        return jsonify({'message': 'You need to be a user'}), 401
    
    media_to_remove = Media.query.filter_by(id=id, owner=user).first()

    if media_to_remove:
        user.owns.remove(media_to_remove)  # Remove media from the user's library
        db.session.commit()
        return jsonify({'message': f'Media with id {id} removed from your library successfully'}), 200
    else:
        return jsonify({'message': f'Media with id {id} not found in your library'}), 404


@bp.route('/update_media/<current_title>/<new_title>', methods=['POST'])
@jwt_required()
def update_media(current_title, new_title):
    username = get_jwt_identity()
    user = User.query.filter_by(username=username).first()

    if not user:
        return jsonify({'message': 'You need to be a user'}), 401
    
    current_title = request.form.get('current_title')
    new_title = request.form.get('new_title')

    if not current_title or not new_title:
        return jsonify({'message': 'Both current and new titles are required'}), 400

    media_to_update = Media.query.filter_by(title=current_title).first()

    if media_to_update:
        media_to_update.title = new_title
        db.session.commit()

        return jsonify({'message': f'Media with title {current_title} updated to {new_title} successfully'}), 200
    else:
        return jsonify({'message': f'Media with title {current_title} not found'}), 404


@bp.route('/create_media', methods=['POST'])
@jwt_required()
def create_media():
    username = get_jwt_identity()
    user = User.query.filter_by(username=username).first()

    if not user:
        return jsonify({'message': 'You need to be a user'}), 401
    
    random_media = Media(
        format=random.choice(['MP3', 'WAV', 'OGG']),
        artist=fake.name(),
        title=fake.catch_phrase(),
        genre=[fake.word() for _ in range(4)],
        lyrics=[fake.sentence() for _ in range(6)],
        audio_base64=base64.b64encode(fake.binary(length=64)).decode('utf-8')
    )

    db.session.add(random_media)
    db.session.commit()

    return jsonify({'message': 'Random media stored successfully'}), 201


@bp.route('/users', methods=['GET'])
@jwt_required()
def list_users():
    username = get_jwt_identity()
    current_user = User.query.filter_by(username=username).first()

    if not current_user:
        return jsonify({'message': 'You need to be a user'}), 401

    all_users = User.query.all()

    users = []
    for user in all_users:
        user_display = {
            'id': user.id,
            'username': user.username,
            'family': user.family_id
        }
        users.append(user_display)

    return jsonify(users), 200
    

@bp.route('/families', methods=['GET'])
@jwt_required()
def list_families():
    username = get_jwt_identity()
    current_user = User.query.filter_by(username=username).first()

    if not current_user:
        return jsonify({'message': 'You need to be a user'}), 401

    all_families = Family.query.all()

    families = []
    for family in all_families:
        family_display = {
            'id': family.id,
            'members': [member.username for member in family.members]
        }
        families.append(family_display)

    return jsonify(families), 200


@bp.route('/family/<id>/join', methods=['PUT'])
@jwt_required()
def join_family(id):
    username = get_jwt_identity()
    user = User.query.filter_by(username=username).first()

    if not user:
        return jsonify({'message': 'You need to be a user'}), 401

    family = Family.query.filter_by(id=id).first()

    if not family:
        return jsonify({'message': f'Family with id {id} not found'}), 404
    
    if family == user.family:
        return jsonify({'message': f'You\'re already part of family with id {id}'}), 400
    
    old_family = user.family
    user.family = family

    if len(old_family.members) == 0:
        db.session.delete(old_family)
    
    family_key = base64.b64decode(family.key.encode('utf-8'))

    encrypted_family_key = SafeSound.encrypt_secret_key(user.public_key.encode('utf-8'), family_key)
    fk_base64 = base64.b64encode(encrypted_family_key).decode('utf-8')
    
    db.session.commit()

    return jsonify({'message': f'You\'re now part of family with id {id}', 'fk': fk_base64}), 200
