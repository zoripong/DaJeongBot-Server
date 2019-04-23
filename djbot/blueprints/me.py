import json

from flask import Blueprint, jsonify, request

from djbot.controllers.data import delete_token, add_token
from djbot.models.models import *

bp = Blueprint('me', __name__, url_prefix='/me')


#   #   #   #   #   #
#     사용자 정보      #
#   #   #   #   #   #
# 닉네임 가져오기
@bp.route('/names/<int:account_id>', methods=['GET'])
def get_name(account_id):
    account = Account.query.filter(Account.id == account_id).all()
    result = {
        "status": "Success",
        "data": {
            "account_id": account_id,
            "name": account[0].name
        }
    }
    return jsonify(result)


# 닉네임 변경
@bp.route('/names', methods=['PUT'])
def update_name():
    content = json.loads(request.data.decode("utf-8"))
    account = Account.query.filter(Account.id == content['account_id']).all()
    account[0].name = content['new_name']
    db.session.commit()

    result = {
        "status": "Success"
    }
    return json.dumps(result)


# 비밀번호 변경
@bp.route('/passwords', methods=['PUT'])
def update_password():
    content = json.loads(request.data.decode("utf-8"))
    account = CustomAccount.query.filter(
        CustomAccount.id == content['account_id']
    ).all()
    account[0].password = content['new_password']
    db.session.commit()
    result = {'status': 'Success'}
    return json.dumps(result)


# 챗봇 캐릭터 변경
@bp.route('/bots', methods=['PUT'])
def update_bots():
    content = json.loads(request.data.decode('utf-8'))
    account = Account.query.filter(Account.id == content['account_id']).first()
    if not account:
        return json.dumps({'status': 'Failed'})
    account.bot_type = content['new_bot_type']
    db.session.commit()
    return json.dumps({'status': 'Success'})


# 설정 시간 가져오기
@bp.route('/times/<int:account_id>', methods=['GET'])
def get_times(account_id):
    account = Account.query.filter(Account.id == account_id).all()
    result = {
        "status": "Success",
        "data": {
            "account_id": account_id,
            "notify_time": account[0].notify_time,
            "ask_time": account[0].ask_time
        }
    }
    return jsonify(result)


# 시간 변경
@bp.route('/times', methods=['PUT'])
def update_times():
    content = json.loads(request.data.decode("utf-8"))
    account = Account.query.filter(Account.id == content['account_id']).all()
    account[0].notify_time = content['new_notify_time']
    account[0].ask_time = content['new_ask_time']
    db.session.commit()

    result = {
        "status": "Success"
    }
    return json.dumps(result)


# 사용자 정보 초기화
@bp.route('/all/<int:account_id>', methods=['DELETE'])
def reset_data(account_id):
    chats = Chat.query.filter(Chat.account_id == account_id).all()
    for chat in chats:
        db.session.delete(chat)

    events = Event.query.filter(Event.account_id == account_id).all()
    for event in events:
        db.session.delete(event)

    db.session.commit()
    result = {
        "status": "Success"
    }
    return json.dumps(result)


#   #   #   #   #   #
#       토큰        #
#   #   #   #   #   #
# 새로운 토큰을 등록
@bp.route('/tokens', methods=['POST'])
def register():
    content = json.loads(request.data.decode("utf-8"))

    tokens = FcmToken.query\
        .filter(FcmToken.account_id == content['account_id'], FcmToken.token == content['fcm_token'])\
        .all()

    if len(tokens) <= 0:
        add_token(content['account_id'], content['fcm_token'])

    result = {
        "status": "Success"
    }
    return json.dumps(result)


# 토큰을 업데이트
@bp.route('/tokens', methods=['PUT'])
def update():
    content = json.loads(request.data.decode("utf-8"))

    token = FcmToken.query\
        .filter(FcmToken.account_id == content['account_id'], FcmToken.token == content['fcm_token']).all()

    token[0].token = content['new_token']
    db.session.commit()

    result = {
        "status": "Success"
    }

    return json.dumps(result)


# 토큰 해제
@bp.route('/tokens/<int:account_id>/<string:fcm_token>', methods=['DELETE'])
def release(account_id, fcm_token):
    delete_token(account_id, fcm_token)
    result = {
        "status": "Success"
    }
    return json.dumps(result)

