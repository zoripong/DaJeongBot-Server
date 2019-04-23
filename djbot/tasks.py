from __future__ import absolute_import

import datetime
import time
from random import randint

from flask import logging
from pyfcm import FCMNotification

import config
from djbot.celery import app
from djbot.controllers.tone import ask_review_message, convert_notification_message, bot_img
from djbot.models.models import *
from djbot.factory import create_app
from celery.utils.log import get_task_logger

# TODO : 일정이 없는 날

flask_app = create_app()
flask_app.app_context().push()
push_service = FCMNotification(api_key=config.FCM_API)
celery = app


@celery.task
def test():
    param = {
        "title": "오늘 일정이 있어요!",
        "message": "야호",
        "data": {
            "status": "Success",
            "result": {}
        }
    }
    logger = get_task_logger('djbot')
    logger.setLevel(logging.INFO)
    logger.info("loggggg")

    token = "c9bJWWrnf_M:APA91bEqLUkgYEo_WskW5gQ-NFLIG_I8_WPVkA5mwtE4iBnqdyGoEmubj2jDmhioSOcKjZwpgd2J79agd59Ky7NMjZc0qurxqZNYaiBAiuANngfgwpblTT3MPGQ3BPgMdbbokOzvBQj2"
    push_service.notify_single_device(
        registration_id=token, data_message=param, content_available=True
    )


# 회원이 등록한 일정의 시작 시간에 안내를 할 수 있도록 메세지를 예약합니다.
@celery.task
def register_calendar_notification():
    # 이벤트 목록 (send is 0)
    # 이벤트에 대한 정보와 회원 account_id
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    print(today)
    events = Event.query.filter(
        Event.notification_send == 0,
        Event.schedule_when == today
    ).order_by(Event.id).all()
    print(len(today))
    logging.info("line 35")

    for event in events:
        # 해당 이벤트를 등록한 계정의 알림 설정 시간과 현재시간을 비교
        accounts = Account.query.filter(Account.id == event.account_id).all()
        logging.info("line 40")
        for account in accounts:
            contents = convert_notification_message(
                event, account.bot_type, randint(0, 3)
            )
            param = {
                "title": "오늘 일정이 있어요!",
                "message": event.schedule_where + "에서 " + event.schedule_what,
                "data": {
                    "status": "Success",
                    "result": {
                        "node_type": 0,
                        "id": event.account_id,
                        "chat_type": 3,
                        "time": str(int(time.time() * 1000)),
                        "img_url": [],
                        "content": contents
                    }
                }
            }
            logging.info("line 58")

            # 해당 일정에 대해 안내 하였음을 업데이트 함
            if send_fcm_message(
                account.notify_time, event.account_id, 0, 3, contents, param
            ):
                event.notification_send = 1
    db.session.commit()


# 회원이 등록한 일정이 끝났을 때 일정에 대한 질문을 예약합니다.
@celery.task
def register_calendar_question():
    # 오늘 일어난 event 중 후기가 null 이면서 사용자의 일기쓰는 시간이 지난 경우
    today = datetime.datetime.now().strftime("%Y-%m-%d")

    accounts = Account.query.all()
    for account in accounts:
        events = Event.query.filter(
            Event.review.is_(None),
            Event.schedule_when == today,
            Event.account_id == account.id
        ).order_by(Event.id).all()

        event_json = []
        for event in events:
            event_json.append({
                "id": event.id,
                "account_id": event.account_id,
                "schedule_when": event.schedule_when,
                "schedule_where": event.schedule_where,
                "schedule_what": event.schedule_what,
                "assign_time": event.assign_time,
                "detail": event.detail,
                "review": event.review,
                "notification_send": event.notification_send,
                "question_send": event.question_send
            })

        content = ask_review_message[0][account.bot_type][randint(0, 3)]

        param = {
            "title": "당신의 하루를 다정봇에게 들려주세요 :)",
            "message": "오늘 " + str(len(events)) + "개의 일정이 있습니다.",
            "data": {
                "status": "Success",
                "result": {
                    "id": account.id,
                    "node_type": 2,
                    "chat_type": 5,
                    "time": str(int(time.time() * 1000)),
                    "img_url": [],
                    "content": content,
                    "events": event_json
                }
            }
        }

        # 해당 일정에 대해 안내 하였음을 업데이트 함
        if send_fcm_message(account.ask_time, account.id, 2, 5, content, param):
            for event in events:
                event.question_send = 1

    db.session.commit()


# TODO TEST
# 생일 축하 메세지
@celery.task
def congratulate_birthday():
    # 이벤트 목록 (send is 0)
    # 이벤트에 대한 정보와 회원 account_id
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    accounts = Account.query.filter(Account.birthday == today).all()
    reg_time = str(int(time.time() * 1000))
    for account in accounts:
        param = {
            "title": "다정봇이 당신의 생일을 축하해줄게요!",
            "message": account.name + "!" + congratulate_birthday[0][account.bot_type],
            "data": {
                "status": "Success",
                "result": {
                    "node_type": 0,
                    "id": account.account_id,
                    "chat_type": 0,
                    "time": reg_time,
                    "img_url": [bot_img["hbd"][account.bot_type]],
                    "content": congratulate_birthday[0][account.bot_type]
                }
            }
        }
        # db
        for content in param["data"]["result"]["content"]:
            chat = Chat(account_id=account.id, content=content, node_type=0,
                        chat_type=0, time=reg_time, isBot=1)
            db.session.add(chat)

        # fcm 알림
        tokens = FcmToken.query.filter(FcmToken.account_id == account.id).all()
        for token in tokens:
            push_service.notify_single_device(
                registration_id=token.token,
                data_message=param,
                content_available=True
            )

    db.session.commit()


# 시간을 비교하여 사용자의 기기에 fcm 알림을 보냅니다.
# param : 비교 시간, 계정 식별번호, 알림 제목, 알림 내용
def send_fcm_message(
    check_time, account_id, node_type, chat_type, contents, param
):
    logging.info("send_fcm_message")
    user_datetime_object = time.strptime(check_time, '%H:%M')
    user_time = datetime.time(
        user_datetime_object[3], user_datetime_object[4]
    ).strftime("%H:%M")
    now_time = datetime.datetime.now().strftime("%H:%M")
    logging.info("now_time > user_time", now_time, user_time)
    if now_time > user_time:
        if chat_type == 4:
            for content in contents:
                chat = Chat(
                    account_id=account_id,
                    content=content,
                    node_type=node_type,
                    chat_type=chat_type,
                    time=str(int(time.time() * 1000)),
                    isBot=1
                )
                db.session.add(chat)
        elif chat_type == 5:
            for content in contents:
                chat = Chat(
                    account_id=account_id,
                    content=content,
                    node_type=node_type,
                    chat_type=chat_type,
                    time=str(int(time.time() * 1000)),
                    isBot=1,
                    carousel_list=str(param['data']['result']['events'])
                )
                db.session.add(chat)

        db.session.commit()
        tokens = FcmToken.query.filter(FcmToken.account_id == account_id).all()
        for token in tokens:
            # send the fcm notification
            print("메세지 전송 얍!")
            logging.info("메세지 전송 : ", token)
            push_service.notify_single_device(
                registration_id=token.token,
                data_message=param,
                content_available=True
            )

        return True
    return False


