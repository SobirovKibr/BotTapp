import asyncio
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database import init_db, SessionLocal, User

# SOZLAMALAR
BOT_TOKEN = "8265563478:AAHI9ywq4QmwcHN3tU2iSZ3iKK2YGaHFB_8"
WEBAPP_URL = "https://sobirovkibr.github.io/BotTapp/" 
ADMIN_ID = 7625297084  # O'zingizning Telegram ID'ingiz

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Lifespan - Startup va Shutdown uchun zamonaviy usul
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ma'lumotlar bazasini ishga tushirish va botni parallel yurgizish
    init_db()
    asyncio.create_task(dp.start_polling(bot))
    print("Bot ishga tushdi...")
    yield
    # Shutdown amallari bu yerga yoziladi (agar kerak bo'lsa)
    print("Bot to'xtadi.")

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"], 
    allow_methods=["*"], 
    allow_headers=["*"]
)

@dp.message(CommandStart())
async def start(message: types.Message):
    user_id = message.from_user.id
    # Referalni tekshirish
    args = message.text.split()
    referrer_id = int(args[1]) if len(args) > 1 and args[1].isdigit() else None

    db = SessionLocal()
    user = db.query(User).filter(User.user_id == user_id).first()
    
    if not user:
        user = User(user_id=user_id, balance=0, referrer_id=referrer_id)
        db.add(user)
        # Referal bonus berish
        if referrer_id:
            ref_user = db.query(User).filter(User.user_id == referrer_id).first()
            if ref_user:
                ref_user.balance += 5000 # 5000 UC Bonus
                try: 
                    await bot.send_message(referrer_id, "Sizda yangi referal! +5000 UC bonus berildi! ✅")
                except: 
                    pass
        db.commit()
    db.close()

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 O'ynash", web_app=WebAppInfo(url=WEBAPP_URL))],
        [InlineKeyboardButton(text="👥 Referal", callback_data="ref_info"), 
         InlineKeyboardButton(text="📋 Vazifalar", callback_data="tasks")]
    ])
    await message.answer(
        f"Salom {message.from_user.first_name}!\nUC yig'uvchi botga xush kelibsiz! ⚡\n\nO'yinni boshlash uchun pastdagi tugmani bosing.", 
        reply_markup=kb
    )

@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        db = SessionLocal()
        count = db.query(User).count()
        db.close()
        await message.answer(f"📊 Statistika:\nJami foydalanuvchilar: {count}")

# XATO TUZATILGAN JOY: Callback_query emas, CallbackQuery bo'lishi kerak
@dp.callback_query(F.data == "ref_info")
async def ref_handler(call: CallbackQuery):
    link = f"https://t.me/ManaUCBot?start={call.from_user.id}"
    await call.message.answer(
        f"🎁 Do'stlarni taklif qiling va UC oling!\n\nSizning taklif havolangiz:\n{link}\n\nHar bir do'stingiz uchun 5000 UC oling!"
    )

@dp.callback_query(F.data == "tasks")
async def tasks_handler(call: CallbackQuery):
    await call.message.answer("📋 Hozircha vazifalar mavjud emas. Tez kunda yangi vazifalar qo'shiladi!")

# API - Ballarni saqlash
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

if __name__ == "__main__":
    import uvicorn
    # Render portni avtomatik beradi, agar bermasa 8000 dan foydalanadi
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
