from fastapi import FastAPI

app = FastAPI()

@app.get('/')
async def root():
    return {'message': "hello"}

async def handle_message():
    return None

async def handle_postbacks():
    return None

async def call_send_API():
    return None

@app.post('/webhook')
async def webhook(tmp):
    print(tmp)
    return None