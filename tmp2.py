from httpx import AsyncClient, HTTPStatusError
import logging
import os
from dotenv import load_dotenv
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
# Cấu hình logging: thời gian, cấp độ, tên module và nội dung
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
FB_SEND_API = "https://graph.facebook.com/v23.0"
# Chặn log chi tiết của httpx, chỉ hiển thị WARNING trở lên
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

async def send_message(base_url: str):
    payload = {
        "recipient": {"id": "9113847768635863"},
        "messaging_type": "RESPONSE",
        "message": {"text": "xin chao"},
    }
    params = {'access_token': 'EAAQR54g2cnMBOwiTKeuarWHzOZBnbKCmGo9ytsyY596ZCEo9pUzY8AUHYmTGLzBTuvw5GbwtR6m5BpKAUX7JocSe9fV8pU7uFmS0AfxQnD3uEbOPffNUXZCSRsnQznUbs2FQSB6A7Hh7RUK5ljOxB0UZAyZCVEY91K1zv5ktx954vBuyZCZC8T4ouAn678QqpejWqoo'}

    async with AsyncClient() as client:
        resp = await client.post(f"{base_url}", params=params, json=payload)

    return resp

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

async def get_conservation(sender_id: str) -> dict | None:
    """
    Lấy thông tin cuộc trò chuyện từ Facebook Graph API.
    Trả về dữ liệu JSON khi thành công, ngược lại log lỗi và trả về None.
    """
    url = f"{FB_SEND_API}/{sender_id}/conversations"
    params = {
        "access_token": PAGE_ACCESS_TOKEN,
        "fields": "messages{from,message}"
    }

    async with AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            logger.info(f"Lấy thông tin cuộc trò chuyện thành công: {data}")
            return data
        except HTTPStatusError as http_err:
            err_text = http_err.response.text
            logger.error(
                f"Lỗi HTTP {http_err.response.status_code} khi lấy thông tin cuộc trò chuyện – {err_text}"
            )
        except Exception as exc:
            logger.exception(f"Lỗi không mong đợi khi lấy thông tin cuộc trò chuyện: {exc}")
    return None

if __name__ == "__main__":
    import asyncio

    base_url = "https://graph.facebook.com/v23.0/462935746912595/messages"  # Thay bằng URL thực tế của bạn
    response = asyncio.run(get_sender_info("9113847768635863"))  # Thay bằng ID người dùng thực tế
    print(response)  # In ra kết quả trả về từ API