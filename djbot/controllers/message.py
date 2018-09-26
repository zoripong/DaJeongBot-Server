import calendar
import datetime
import time
from random import randint

from flask import jsonify

from djbot.controllers import danbee
from djbot.controllers.memory import get_memory
from djbot.controllers.schedule import register_event, update_event
from djbot.controllers.tone import danbee_message, welcome_message, bot_img
from djbot.models.models import *
from config import NODE_TYPE

#   #   #   #   #   #
#  메세지 컨트롤러  #
#   #   #   #   #   #


def add_message_for_new_user(account_id, bot_type):
    print("add_message_for_new_user")
    ts = calendar.timegm(time.gmtime())
    # 챗봇 타입에 따라 말투를 달리함
    content = welcome_message[bot_type]
    print(content)
    chat = Chat(account_id=account_id, content=content, node_type=0, chat_type=0, time=str(ts), isBot=1)
    db.session.add(chat)
    db.session.commit()


# 답장을 주는 부분
def reply_message(content, chat_type):
    current = datetime.datetime.now()
    print("current : "+ current.strftime("%Y-%m-%d"))
    # 챗봇
    if chat_type == 6:
        param = {
            "event_id": content['content']
        }
        reply = danbee.message_with_param("이유리바보", param)
    else:
        reply = danbee.message_with_response(content['content'], content['response'])
    reply_result = reply['responseSet']['result']['result']
    result_json = {
        "status": "Failed",
    }
    for result in reply_result:
        img_url = result['imgRoute']
        print(img_url)
        if img_url is not None and img_url != "":
            result['imgRoute'] = bot_img[img_url][content['bot_type']]
            chat = Chat(account_id=content['account_id'], content=bot_img[img_url][content['bot_type']],
                        node_type=NODE_TYPE['img'], chat_type=content['chat_type'],
                        time=str(int(time.time() * 1000)), isBot=1)
            db.session.add(chat)

        if reply['responseSet']['result']['ins_id'] == "" \
                and reply['responseSet']['result']['ref_intent_id'] == "":
            result_json = {
                "status": "Intent is not Found",
            }

        # 챗봇 타입에 따라 말투를 달리함
        primitive_message = result['message']
        result['message'] = danbee_message[result['message']][content['bot_type']][randint(0, 3)]
        node_type = result['nodeType']
        print("primitive : " + primitive_message)
        # 커스텀 챗봇으로 넘김
        if primitive_message == "SpeakNode_1533088132355":
            # 추억 회상
            result_json = get_memory(reply, content, current)
        else:
            if primitive_message == "SpeakNode_1533084803517":
                # 일정 등록
                register_event(reply, result, content['account_id'])
            # elif primitive_message == "SpeakNode_1537355664283":
                #TODO 일정이 있는지 없는지
                # 있으면 REQUEST 요청 후 RETURN
                # 없으면 그냥 TEXT RETURN
            elif primitive_message == "SpeakNode_1537356062991":
                # 일정 수정
                update_event(reply)
            result_json = reply

            # node type
            # speak=0 slot=1 carousel=2
            chat = Chat(account_id=content['account_id'], content=result['message'], node_type=NODE_TYPE[node_type],
                        chat_type=content['chat_type'], time=str(int(time.time() * 1000)), isBot=1)
            db.session.add(chat)

    db.session.commit()
    print(result_json)
    return jsonify(result_json)