import asyncio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from database import init_db, SessionLocal, User
import os

# SOZLAMALAR
BOT_TOKEN = "8265563478:AAHI9ywq4QmwcHN3tU2iSZ3iKK2YGaHFB_8"
WEBAPP_URL = "https://sobirovkibr.github.io/MiniAppWeb/" # GitHub Pages linki

app = FastAPI()

# CORS - Frontend (GitHub) bilan ulanish uchun ruxsat
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@app.on_event("startup")
async def startup():
    init_db()

@dp.message(CommandStart())
async def start(message: types.Message):
    user_id = message.from_user.id
    db = SessionLocal()
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        user = User(user_id=user_id, balance=0)
        db.add(user)
        db.commit()
    db.close()

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Play UC", web_app=WebAppInfo(url=WEBAPP_URL))]
    ])
    await message.answer(f"Salom {message.from_user.first_name}! UC yig'ishni boshlang!", reply_markup=kb)

@app.post("/update_balance")
async def update_balance(request: Request):
    data = await request.json()
    uid, pts = data.get("user_id"), data.get("points")
    db = SessionLocal()
    user = db.query(User).filter(User.user_id == uid).first()
    if user:
        user.balance += pts
        db.commit()
    db.close()
    return {"ok": True}

async def run_bot():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import uvicorn
    # Botni FastAPI bilan parallel yurgizish
    loop = asyncio.get_event_loop()
    loop.create_task(run_bot())
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)