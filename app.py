import os
import sys
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from httpx import AsyncClient, HTTPStatusError
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
FB_SEND_API = "https://graph.facebook.com/v23.0/462935746912595/messages"

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
                await send_message(sender_id, f"Bạn đã gửi: '{text}'")

    return {"status": "ok"}

async def send_message(recipient_id: str, text: str) -> dict | None:
    """
    Gửi tin nhắn qua Facebook Send API.
    Trả về dữ liệu JSON khi thành công, ngược lại log lỗi và trả về None.
    """
    url = f"{FB_SEND_API}?access_token={PAGE_ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": recipient_id},
        "messaging_type": "RESPONSE",
        "message": {"text": text},
    }
    logger.debug(f"Chuẩn bị gửi tin nhắn tới {recipient_id}: {text}")

    async with AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            logger.info(f"Gửi tin nhắn thành công tin nhắn '{text}' tới {recipient_id}")
            return data
        except HTTPStatusError as http_err:
            err_text = http_err.response.text
            logger.error(
                f"Lỗi HTTP {http_err.response.status_code} khi gửi tin nhắn – {err_text}"
            )
        except Exception as exc:
            logger.exception(f"Lỗi không mong đợi khi gửi tin nhắn: {exc}")
    return None
