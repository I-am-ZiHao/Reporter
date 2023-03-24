from django.shortcuts import render
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from linebot import LineBotApi, WebhookParser, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

from pymongo import MongoClient

line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(settings.LINE_CHANNEL_SECRET)

# mongodb
client = MongoClient(settings.MONGO_DB)
database = client.test
collection = database.test1


@csrf_exempt
def callback(request):

    if request.method == "POST":
        signature = request.META["HTTP_X_LINE_SIGNATURE"]
        body = request.body.decode("utf-8")

        try:
            handler.handle(body, signature)
        except InvalidSignatureError:
            return HttpResponseForbidden()
        except LineBotApiError:
            return HttpResponseBadRequest()
        return HttpResponse()
    else:
        return HttpResponseBadRequest()


@handler.add(event=MessageEvent, message=TextMessage)
def handle_message(event: MessageEvent):
    message = event.message.text

    try:
        group_id = event.source.group_id
    except:
        group_id = event.source.user_id

    if message == "使用說明":
        result = "初次使用請先輸入本班五碼學號範圍，格式如下：\n學號範圍：xxxxx-xxxxx\n\n接著輸入「確認學號範圍」檢查輸入是否正確。\n\n完成以上動作後可開始回報，格式：\n時間：20:00\n學號：xxxxx\n姓名：xxx\n電話：09xxxxxxxx\n現在位置：在家\n現在在幹嘛：休息\n跟誰：家人\n身體狀況：良好\n\n輸入「他媽的回報」，機器人便會按照學號順序進行統整；若尚未回報完，則機器人會回覆尚未回報之學號。\n\n輸入「使用說明」，機器人會回傳以上內容。"
        line_bot_api.reply_message(
            reply_token=event.reply_token, messages=TextSendMessage(text=result)
        )

    elif message[:5] == "學號範圍：":
        start = int(message[message.find("圍") + 2 : message.find("圍") + 7])
        end = int(message[message.find("圍") + 8 :])
        ids = [start + i for i in range(end - start + 1)]
        data = collection.find_one({"group_id": group_id})

        if not data:  # 首次輸入學號範圍
            new_document = {"group_id": group_id, "message": {}, "studentIDs": ids}
            collection.insert_one(new_document)
        else:  # 更新學號範圍
            data["studentIDs"] = ids
            collection.update_one({"group_id": group_id}, {"$set": data})

    elif message == "確認學號範圍":
        result = ""
        data = collection.find_one({"group_id": group_id})

        if not data or "studentIDs" not in data.keys():
            result += "尚未輸入學號範圍，請參閱使用說明"
        else:
            result += "本班學號：\n"
            for id in data["studentIDs"]:
                result += str(id) + "、 "
            result = result[:-2] + "\n\n若學號有誤，請參照使用說明重新輸入。"

        line_bot_api.reply_message(
            reply_token=event.reply_token, messages=TextSendMessage(text=result)
        )

    elif (
        "時間" in message
        and "學號" in message
        and "姓名" in message
        and "電話" in message
        and "現在位置" in message
    ):
        person_id = message[message.find("學號") + 3 : message.find("學號") + 8]
        data = collection.find_one({"group_id": group_id})

        if not data:  # 首次輸入學號範圍前就有人回報
            new_document = {"group_id": group_id, "message": {person_id: message}}
            collection.insert_one(new_document)
        else:
            data["message"][person_id] = message
            collection.update_one({"group_id": group_id}, {"$set": data})

    elif message == "他媽的回報":
        result = ""
        data = collection.find_one({"group_id": group_id})

        if not data or "studentIDs" not in data.keys():  # 避免初次使用前就有人講到關鍵字或輸入學號範圍前就有人先回報
            result += "尚未輸入學號範圍，請參閱使用說明  "

        elif len(data["message"].keys()) < len(data["studentIDs"]):  # 未回報完
            result += "尚未回報：\n"
            for id in data["studentIDs"]:
                if str(id) not in list(data["message"].keys()):
                    result += str(id) + "、 "

        else:  # 已回報完
            for key in sorted(data["message"].keys()):
                result += data["message"][key] + "\n\n"
            data["message"] = {}
            collection.update_one({"group_id": group_id}, {"$set": data})

        line_bot_api.reply_message(
            reply_token=event.reply_token, messages=TextSendMessage(text=result[:-2])
        )
