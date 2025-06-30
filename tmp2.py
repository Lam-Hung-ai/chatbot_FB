from httpx import AsyncClient

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

if __name__ == "__main__":
    import asyncio

    base_url = "https://graph.facebook.com/v23.0/462935746912595/messages"  # Thay bằng URL thực tế của bạn
    response = asyncio.run(send_message(base_url))
    print(response.text)  # In ra kết quả trả về từ API