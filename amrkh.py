import asyncio
import sqlite3
import logging
import matplotlib.pyplot as plt
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta7

# Telegram bot token
TOKEN = "7714704320:AAELH2H3UvQOwbczSfYdhvKKlCI6AwWHYQw"

# Bot va dispatcher yaratish
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Bazaga ulanish
conn = sqlite3.connect("data.db")
cursor = conn.cursor()

# Jadval yaratish
cursor.execute("""
    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        shop_id INTEGER,
        amount INTEGER,
        date TEXT
    )
""")
conn.commit()

# Foydalanuvchi ma'lumotlarini saqlash uchun
user_data = {}

# Klaviatura tugmalari
markup = ReplyKeyboardMarkup(resize_keyboard=True)
markup.add(KeyboardButton("📊 Kunlik Hisobot"), KeyboardButton("📅 Haftalik Hisobot"))

# Raqamni qabul qilish
@dp.message_handler(lambda message: message.text.isdigit())
async def get_amount(message: types.Message):
    user_data[message.from_user.id] = {"amount": int(message.text)}
    await message.reply("Bu qaysi do'kon?", reply_markup=types.ReplyKeyboardRemove())

# Do‘kon raqamini olish
@dp.message_handler(lambda message: message.text.isdigit(), state=None)
async def get_shop_id(message: types.Message):
    user_id = message.from_user.id
    if user_id in user_data:
        amount = user_data[user_id]["amount"]
        shop_id = int(message.text)
        date = datetime.now().strftime("%Y-%m-%d")

        cursor.execute("INSERT INTO sales (shop_id, amount, date) VALUES (?, ?, ?)", (shop_id, amount, date))
        conn.commit()
        
        await message.reply(f"✅ {amount} so‘m {shop_id}-do‘konga yozildi.", reply_markup=markup)
        del user_data[user_id]

# Kunlik hisobotni chiqarish
async def send_daily_report():
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("SELECT shop_id, SUM(amount) FROM sales WHERE date = ? GROUP BY shop_id", (today,))
    data = cursor.fetchall()

    if not data:
        return

    report = "**📊 Kunlik Hisobot:**\n"
    shop_names = []
    amounts = []
    
    for shop_id, total in data:
        report += f"🏪 Do'kon {shop_id}: {total} so‘m\n"
        shop_names.append(f"Shop {shop_id}")
        amounts.append(total)

    await bot.send_message(YOUR_CHAT_ID, report)  # O'zingizning chat ID ni yozing
    create_chart(shop_names, amounts, "Kunlik Hisobot")
    await bot.send_photo(YOUR_CHAT_ID, photo=open("chart.png", "rb"))

# Haftalik hisobotni chiqarish
async def send_weekly_report():
    start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    cursor.execute("SELECT shop_id, SUM(amount) FROM sales WHERE date >= ? GROUP BY shop_id", (start_date,))
    data = cursor.fetchall()

    if not data:
        return

    report = "**📅 Haftalik Hisobot:**\n"
    shop_names = []
    amounts = []

    for shop_id, total in data:
        report += f"🏪 Do'kon {shop_id}: {total} so‘m\n"
        shop_names.append(f"Shop {shop_id}")
        amounts.append(total)

    await bot.send_message(YOUR_CHAT_ID, report)
    create_chart(shop_names, amounts, "Haftalik Hisobot")
    await bot.send_photo(YOUR_CHAT_ID, photo=open("chart.png", "rb"))

# Diagramma yaratish
def create_chart(labels, values, title):
    plt.figure(figsize=(6, 4))
    plt.bar(labels, values, color="blue")
    plt.xlabel("Do'konlar")
    plt.ylabel("Summa")
    plt.title(title)
    plt.xticks(rotation=45)
    plt.savefig("chart.png")
    plt.close()

# Scheduler ishga tushirish
scheduler = AsyncIOScheduler()
scheduler.add_job(send_daily_report, "cron", hour=20, minute=0)
scheduler.add_job(send_weekly_report, "cron", day_of_week="mon", hour=9, minute=0)
scheduler.start()

# Botni ishga tushirish
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    executor.start_polling(dp, skip_updates=True)
