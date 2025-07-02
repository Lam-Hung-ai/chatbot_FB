import os
import sys
import logging

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse

from pydantic import BaseModel

from httpx import AsyncClient, HTTPStatusError

from langchain_core.chat_history import InMemoryChatMessageHistory

from dotenv import load_dotenv

# Cấu hình logging: thời gian, cấp độ, tên module và nội dung
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
# Chặn log chi tiết của httpx, chỉ hiển thị WARNING trở lên
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Load biến môi trường từ file .env
load_dotenv()
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
if not PAGE_ACCESS_TOKEN or not VERIFY_TOKEN:
    logger.critical("Thiếu PAGE_ACCESS_TOKEN hoặc VERIFY_TOKEN trong .env, ứng dụng sẽ dừng.")
    sys.exit("Thiếu PAGE_ACCESS_TOKEN hoặc VERIFY_TOKEN trong .env")

# URL endpoint của Facebook Send API
FB_SEND_API = "https://graph.facebook.com/v23.0"

# Khởi tạo ứng dụng FastAPI
app = FastAPI()

# Định nghĩa mô hình dữ liệu nhận từ webhook
class Entry(BaseModel):
    id: str
    time: int
    messaging: list

class WebhookPayload(BaseModel):
    object: str
    entry: list[Entry]

@app.get('/')
async def root():
    """
    Endpoint kiểm tra server còn hoạt động.
    """
    logger.info("Người dùng truy cập endpoint gốc.")
    return {'message': "hello"}

@app.get("/webhook")
async def verify_webhook(request: Request):
    """
    Xác minh webhook với Facebook.
    Kiểm tra hub.mode và hub.verify_token, trả về hub.challenge nếu đúng.
    """
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    logger.debug(f"Xác minh webhook: mode={mode}, token={token}")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        logger.info("Xác minh webhook thành công.")
        return PlainTextResponse(challenge)
    else:
        logger.warning("Xác minh webhook thất bại.")
        raise HTTPException(status_code=403, detail="Xác minh thất bại")

async def get_sender_info(sender_id: str) -> dict | None:
    """
    Lấy thông tin người dùng từ Facebook Graph API.
    Trả về dữ liệu JSON khi thành công, ngược lại log lỗi và trả về None.
    """
    url = f"{FB_SEND_API}/{sender_id}"
    params = {
        "fields": "first_name,last_name",
        "access_token": PAGE_ACCESS_TOKEN
    }

    async with AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            logger.info(f"Lấy thông tin người dùng thành công: {data}")
            return data
        except HTTPStatusError as http_err:
            err_text = http_err.response.text
            logger.error(
                f"Lỗi HTTP {http_err.response.status_code} khi lấy thông tin người dùng – {err_text}"
            )
        except Exception as exc:
            logger.exception(f"Lỗi không mong đợi khi lấy thông tin người dùng: {exc}")
    return None

async def get_info_conservation(sender_id: str) -> str | None:
    """
    Lấy ID cuộc trò chuyện từ Facebook Graph API.
    Trả về ID cuộc trò chuyện nếu thành công, ngược lại log lỗi và trả về None.
    """
    url = f"{FB_SEND_API}/462935746912595/conversations"
    params = {
        "access_token": PAGE_ACCESS_TOKEN,
        "fields": "id,senders"
    }

    async with AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            conversations = data["data"]
            for conversation in conversations:
                for sender in conversation['senders']['data']:
                    conversation_id = conversation['id']
                    if sender['id'] == sender_id:
                        logger.info(f"Tìm thấy thành công sender ID: {sender_id} có conversation ID: {conversation_id} và tên là: {sender.get('name', 'N/A')}")
                        return (sender_id, conversation_id)

        except HTTPStatusError as http_err:
            err_text = http_err.response.text
            logger.error(
                f"Lỗi HTTP {http_err.response.status_code} khi lấy thông tin cuộc trò chuyện của {sender_id}: {err_text}"
            )
        except Exception as exc:
            logger.exception(f"Lỗi không mong đợi khi lấy hông tin cuộc trò chuyện của {sender_id}: {exc}")
    return (None, None)

async def get_conservation(conversation_id: str, sender_id: str, limit: int= 40) -> dict | None:
    """
    Lấy thông tin cuộc trò chuyện từ Facebook Graph API.
    Trả về dữ liệu JSON khi thành công, ngược lại log lỗi và trả về None.
    """
    url = f"{FB_SEND_API}/{conversation_id}"
    params = {
        "access_token": PAGE_ACCESS_TOKEN,
        "fields": "messages.limit("+ str(limit) +"){message,from}"
    }
    async with AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            messages = data["messages"]['data']
            messages.reverse()
            history = InMemoryChatMessageHistory()
            for message in messages:
                if message['from']['id'] == sender_id:
                    history.add_user_message(message['message'])
                else:
                    history.add_ai_message(message['message'])

            logger.info(f"Lấy thông tin cuộc trò chuyện thành công cho {sender_id} với ID cuộc trò chuyện {conversation_id}")
            return history.messages.copy()
        except HTTPStatusError as http_err:
            err_text = http_err.response.text
            logger.error(
                f"Lỗi HTTP {http_err.response.status_code} khi lấy thông tin cuộc trò chuyện – {err_text}"
            )
        except Exception as exc:
            logger.exception(f"Lỗi không mong đợi khi lấy thông tin cuộc trò chuyện: {exc}")
    return None

async def send_message(recipient_id: str, text: str) -> dict | None:
    """
    Gửi tin nhắn qua Facebook Send API.
    Trả về dữ liệu JSON khi thành công, ngược lại log lỗi và trả về None.
    """

    params = {"access_token": PAGE_ACCESS_TOKEN}
    url = f"{FB_SEND_API}/462935746912595/messages"
    payload = {
        "recipient": {"id": recipient_id},
        "messaging_type": "RESPONSE",
        "message": {"text": text},
    }

    async with AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.post(url, json=payload, params=params)
            resp.raise_for_status()
            data = resp.json()
            logger.info(f"Gửi tin nhắn thành công tin nhắn tới {recipient_id}")
            return data
        except HTTPStatusError as http_err:
            err_text = http_err.response.text
            logger.error(
                f"Lỗi HTTP {http_err.response.status_code} khi gửi tin nhắn – {err_text}"
            )
        except Exception as exc:
            logger.exception(f"Lỗi không mong đợi khi gửi tin nhắn: {exc}")
    return None

@app.post("/webhook")
async def handle_messages(payload: WebhookPayload):
    """
    Xử lý tin nhắn và postback gửi đến webhook.
    """
    logger.info(f"Nhận payload: object={payload.object}")
    if payload.object != "page":
        logger.error("Payload không phải object 'page'.")
        raise HTTPException(status_code=400, detail="Loại object không hợp lệ")

    for entry in payload.entry:
        for event in entry.messaging:
            sender_id = event.get("sender", {}).get("id")
            if not sender_id:
                logger.debug("Không tìm thấy sender ID, bỏ qua event này.")
                continue

            if "message" in event:
                text = event["message"].get("text", "")
                logger.info(f"Tin nhắn từ {sender_id}: {text}")
                conversation_info = await get_info_conservation(sender_id)
                if conversation_info is None:
                    logger.error(f"Không tìm thấy thông tin cuộc trò chuyện cho {sender_id}")
                    continue
                sender_id, conversation_id = conversation_info
                if conversation_id is None:
                    logger.error(f"Không tìm thấy ID cuộc trò chuyện cho {sender_id}")
                    continue
                messages = await get_conservation(conversation_id, sender_id)
                if messages is None:
                    logger.error(f"Không thể lấy thông tin cuộc trò chuyện cho {sender_id} với ID {conversation_id}")
                    continue
                print(messages)
                # Gửi tin nhắn phản hồi
                await send_message(sender_id, f"Bạn đã gửi: '{text}'")

    return {"status": "ok"}