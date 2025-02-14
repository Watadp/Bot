import pandas as pd
from datetime import datetime
import discord
from discord.ext import commands
import re
import os
import matplotlib.pyplot as plt
from flask import Flask
from threading import Thread

# Tạo Flask Server để giữ bot online
app = Flask('')


@app.route('/')
def home():
    return "Bot is running!"


def run():
    app.run(host='0.0.0.0', port=8080)


def keep_alive():
    t = Thread(target=run)
    t.start()


# Tên file Excel
EXCEL_FILE = "finance.xlsx"


# Tạo file nếu chưa tồn tại
def initialize_excel():
    if not os.path.exists(EXCEL_FILE):
        writer = pd.ExcelWriter(EXCEL_FILE, engine='xlsxwriter')
        writer.close()


initialize_excel()

keywords_income = [
    "thu nhập", "lương", "kiếm được", "nhận tiền", "có tiền", "cộng vào",
    "thưởng", "được", "nhận"
]
keywords_expense = [
    "chi tiêu", "mua", "trả tiền", "hết tiền", "tiêu", "mất", "bị trừ", "trả",
    "rút", "chi"
]


def add_transaction(type, amount, description):
    sheet_name = datetime.now().strftime('%m-%Y')
    try:
        df = pd.read_excel(EXCEL_FILE, sheet_name=sheet_name)
    except:
        df = pd.DataFrame(columns=["type", "amount", "description", "date"])

    new_transaction = pd.DataFrame([{
        "type":
        type,
        "amount":
        amount * 1000,
        "description":
        description,
        "date":
        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }])

    df = pd.concat([df, new_transaction], ignore_index=True)
    with pd.ExcelWriter(EXCEL_FILE,
                        engine='openpyxl',
                        mode='a',
                        if_sheet_exists='replace') as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)
    print("Giao dịch đã thêm!")


def get_balance(month_year=None):
    if month_year is None:
        month_year = datetime.now().strftime('%m-%Y')
    try:
        df = pd.read_excel(EXCEL_FILE, sheet_name=month_year)
        income = df[df["type"] == "income"]["amount"].sum()
        expense = df[df["type"] == "expense"]["amount"].sum()
        return (income - expense) / 1000
    except:
        return "Không có dữ liệu cho tháng này!"


def get_all_transactions(month_year=None):
    if month_year is None:
        month_year = datetime.now().strftime('%m-%Y')
    try:
        df = pd.read_excel(EXCEL_FILE, sheet_name=month_year)
        if df.empty:
            return "Không có dữ liệu giao dịch!"
        return df.to_string(index=True)
    except:
        return "Không có dữ liệu giao dịch cho tháng này!"


def generate_chart(month_year=None):
    if month_year is None:
        month_year = datetime.now().strftime('%m-%Y')
    try:
        df = pd.read_excel(EXCEL_FILE, sheet_name=month_year)
        summary = df.groupby("type")["amount"].sum()
        if summary.empty:
            return None
        plt.figure(figsize=(6, 6))
        plt.pie(summary,
                labels=summary.index,
                autopct='%1.1f%%',
                startangle=140)
        plt.title(f"Tổng quan thu nhập và chi tiêu ({month_year})")
        plt.savefig("finance_chart.png")
        plt.close()
        return "finance_chart.png"
    except:
        return None


# Thiết lập bot Discord
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

TOKEN = "MTMzODU1MTQwODEwNTg4MTYyMA.G3ILc9.gHC03mA3vD85P2LEJXptZg78_nGIzVOlflxuEw"
USER_ID = 789500657739890759  # Thay bằng ID người dùng Discord của bạn


@bot.event
async def on_ready():
    print(f"Bot đã đăng nhập thành công với tên: {bot.user}")
    user = await bot.fetch_user(USER_ID)
    if user:
        await user.send(
            "Bot đã mở! Gõ giao dịch hoặc dùng !bot_help để xem lệnh.")


@bot.command()
async def bot_help(ctx):
    help_message = (
        "**Danh sách lệnh:**\n"
        "- **Ghi giao dịch:** Nhập số tiền cùng từ khóa liên quan như 'lương', 'mua', 'chi tiêu'\n"
        "- **Kiểm tra số dư:** Gõ '!balance [MM/YYYY]'\n"
        "- **Kiểm tra tất cả giao dịch:** Gõ '!check [MM/YYYY]'\n"
        "- **Tạo biểu đồ:** Gõ '!chart [MM/YYYY]'\n")
    await ctx.send(help_message)


@bot.command()
async def balance(ctx, month_year: str = None):
    result = get_balance(month_year)
    await ctx.send(
        f"💰 Số dư {month_year or datetime.now().strftime('%m-%Y')}: {result}k")


@bot.command()
async def check(ctx, month_year: str = None):
    transactions = get_all_transactions(month_year)
    await ctx.send(f"```{transactions}```")


@bot.command()
async def chart(ctx, month_year: str = None):
    chart_file = generate_chart(month_year)
    if chart_file:
        await ctx.send(file=discord.File(chart_file))
    else:
        await ctx.send("Không có dữ liệu để tạo biểu đồ cho tháng này!")


@bot.event
async def on_message(message):
    if message.author.id == USER_ID:
        msg_content = message.content.lower()
        amount_match = re.search(r'\d+', msg_content)
        amount = int(amount_match.group()) if amount_match else None

        type_transaction = None
        for keyword in keywords_income:
            if keyword in msg_content:
                type_transaction = "income"
                break
        for keyword in keywords_expense:
            if keyword in msg_content:
                type_transaction = "expense"
                break

        if amount and type_transaction:
            add_transaction(type_transaction, amount, message.content)
            await message.author.send(
                f"Đã ghi nhận giao dịch: {type_transaction} {amount}k - {message.content}"
            )
    await bot.process_commands(message)


keep_alive()

# Chạy bot
if __name__ == "__main__":
    bot.run(TOKEN)
