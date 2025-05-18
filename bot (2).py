import asyncio
import json
import os
import random
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

API_TOKEN = '7506855342:AAFgcMp-Zys1U2ttfUxv4QfI7iIvGdavnvw'
ADMIN_ID = 7420792981

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# === File Helpers ===
def read_json(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def write_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

# === Utils ===
def get_random_ad():
    ads = [f for f in os.listdir("ads") if f.endswith(".json")]
    if not ads:
        return None
    file = random.choice(ads)
    data = read_json(f"ads/{file}")
    return data, file.replace(".json", "")

def get_film(fid):
    return read_json(f"files/{fid}.json")

def add_ad_view(ad_id, uid):
    views = read_json("views.json", {})
    views.setdefault(ad_id, [])
    if uid not in views[ad_id]:
        views[ad_id].append(uid)
        write_json("views.json", views)

def get_ad_views(ad_id):
    views = read_json("views.json", {})
    return len(views.get(ad_id, []))

# === Keyboards ===
panel_kb = ReplyKeyboardMarkup(resize_keyboard=True).add(
    KeyboardButton("➕ Филм"), KeyboardButton("➕ Реклама"),
).add(
    KeyboardButton("📊 Статистика"), KeyboardButton("🗑️ Тоза кардан")
)

# === State Tracking ===
user_state = {}

# === Handlers ===
@dp.message_handler(commands=['start'])
async def handle_start(message: types.Message):
    args = message.get_args()
    if not args:
        await message.answer("Истифодаи нодуруст.")
        return
    film = get_film(args)
    if not film:
        await message.answer("Филм ёфт нашуд.")
        return

    ad_data = get_random_ad()
    ad_msg = None
    if ad_data:
        ad, ad_id = ad_data
        ad_msg = await bot.send_video(message.chat.id, ad["file_id"], caption=ad["caption"], protect_content=True)
        add_ad_view(ad_id, message.chat.id)

    await asyncio.sleep(3)
    await bot.send_video(message.chat.id, film["file_id"], caption=film["caption"], protect_content=True)

    if ad_msg:
        await asyncio.sleep(12)
        try:
            await bot.delete_message(message.chat.id, ad_msg.message_id)
        except:
            pass

@dp.message_handler(commands=['panel'])
async def panel(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        user_state[message.chat.id] = None
        await message.answer("Панели идоракунӣ:", reply_markup=panel_kb)

@dp.message_handler(lambda m: m.from_user.id == ADMIN_ID)
async def admin_controls(message: types.Message):
    cid = message.chat.id
    if message.text == "➕ Филм":
        user_state[cid] = "add_film"
        await message.answer("Филмро бо caption фиристед.")
    elif message.text == "➕ Реклама":
        user_state[cid] = "add_ad"
        await message.answer("Рекламаро бо caption фиристед.")
    elif message.text == "📊 Статистика":
        ads = [f for f in os.listdir("ads") if f.endswith(".json")]
        for af in ads:
            ad_id = af.replace(".json", "")
            ad = read_json(f"ads/{af}")
            views = get_ad_views(ad_id)
            await bot.send_video(cid, ad["file_id"], caption=f"{ad['caption']}

Ин рекламаро {views} нафар дидааст.")
    elif message.text == "🗑️ Тоза кардан":
        ads = [f for f in os.listdir("ads") if f.endswith(".json")]
        for af in ads:
            ad_id = af.replace(".json", "")
            ad = read_json(f"ads/{af}")
            views = get_ad_views(ad_id)
            kb = InlineKeyboardMarkup().add(InlineKeyboardButton("❌ Хориҷ кардан", callback_data=f"delete_{ad_id}"))
            await bot.send_video(cid, ad["file_id"], caption=f"{ad['caption']}

Дидаанд: {views} нафар", reply_markup=kb)

@dp.message_handler(content_types=types.ContentType.VIDEO)
async def receive_video(message: types.Message):
    cid = message.chat.id
    if cid != ADMIN_ID or cid not in user_state:
        return
    state = user_state.get(cid)
    file_id = message.video.file_id
    caption = message.caption or ""
    if state == "add_ad":
        uid = f"ad_{int(asyncio.get_event_loop().time())}"
        write_json(f"ads/{uid}.json", {"file_id": file_id, "caption": caption})
        await message.answer("Реклама сабт шуд.")
    elif state == "add_film":
        uid = f"{int(asyncio.get_event_loop().time())}"
        write_json(f"files/{uid}.json", {"file_id": file_id, "caption": caption})
        link = f"https://t.me/GEM_SERIESTv_bot?start={uid}"
        await message.answer(f"Линк тайёр аст:
{link}")
    user_state[cid] = None

@dp.callback_query_handler(lambda c: c.data.startswith("delete_"))
async def handle_delete(callback_query: types.CallbackQuery):
    ad_id = callback_query.data.replace("delete_", "")
    path = f"ads/{ad_id}.json"
    if os.path.exists(path):
        os.remove(path)
        await callback_query.message.answer(f"Реклама бо ID {ad_id} удалит шуд.")
    await callback_query.answer()

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)