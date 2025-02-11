import pandas as pd
import requests
from datetime import datetime
import discord
from discord.ext import commands
import re
import os
import matplotlib.pyplot as plt

# Tên file Excel
EXCEL_FILE = "finance.xlsx"

# Tạo file nếu chưa tồn tại
def initialize_excel():
    if not os.path.exists(EXCEL_FILE):
        df = pd.DataFrame(columns=["type", "amount", "description", "date"])
        df.to_excel(EXCEL_FILE, index=False)

initialize_excel()

keywords_income = ["thu nhập", "lương", "kiếm được", "nhận tiền", "có tiền", "cộng vào", "thưởng", "được", "nhận"]
keywords_expense = ["chi tiêu", "mua", "trả tiền", "hết tiền", "tiêu", "mất", "bị trừ", "trả", "rút", "chi"]

def add_transaction(type, amount, description):
    df = pd.read_excel(EXCEL_FILE)
    new_transaction = pd.DataFrame([{ "type": type, "amount": amount * 1000, "description": description, "date": datetime.now().strftime('%Y-%m-%d %H:%M:%S') }])
    df = pd.concat([df, new_transaction], ignore_index=True)
    df.to_excel(EXCEL_FILE, index=False)
    print("Giao dịch đã thêm!")

def get_balance():
    df = pd.read_excel(EXCEL_FILE)
    income = df[df["type"] == "income"]["amount"].sum()
    expense = df[df["type"] == "expense"]["amount"].sum()
    return (income - expense) / 1000

def list_transactions():
    df = pd.read_excel(EXCEL_FILE)
    print(df)

def clear_transactions():
    df = pd.DataFrame(columns=["type", "amount", "description", "date"])
    df.to_excel(EXCEL_FILE, index=False)
    print("Dữ liệu đã được xóa!")

def generate_chart():
    df = pd.read_excel(EXCEL_FILE)
    summary = df.groupby("type")["amount"].sum()
    
    if summary.empty:
        print("Không có dữ liệu để tạo biểu đồ!")
        return None
    
    plt.figure(figsize=(6, 6))
    plt.pie(summary, labels=summary.index, autopct='%1.1f%%', startangle=140)
    plt.title("Tổng quan thu nhập và chi tiêu")
    plt.savefig("finance_chart.png")
    plt.close()
    print("Biểu đồ đã được tạo!")
    return "finance_chart.png"

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
        await user.send("Bot đã mở! !help để check lệnh")
        print("Đã gửi tin nhắn thông báo bot đã mở.")

@bot.command()
async def help(ctx):
    help_message = (
        "**Danh sách lệnh:**\n"
        "- **Ghi giao dịch:** Nhập số tiền cùng từ khóa liên quan như 'lương', 'mua', 'chi tiêu'\n"
        "- **Kiểm tra số dư:** Gõ 'số dư' hoặc 'balance'\n"
        "- **Xóa dữ liệu:** Gõ 'xóa dữ liệu' hoặc 'clear data'\n"
        "- **Tạo biểu đồ:** Gõ 'biểu đồ' hoặc 'chart'\n"
        "- **Trợ giúp:** Gõ '!help' để xem danh sách lệnh"
    )
    await ctx.send(help_message)

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
            await message.author.send(f"Đã ghi nhận giao dịch: {type_transaction} {amount}k - {message.content}")
        elif "số dư" in msg_content or "balance" in msg_content:
            balance = get_balance()
            await message.author.send(f"Số dư hiện tại: {balance}")
        elif "biểu đồ" in msg_content or "chart" in msg_content:
            chart_file = generate_chart()
            if chart_file:
                await message.author.send(file=discord.File(chart_file))
            else:
                await message.author.send("Không có dữ liệu để tạo biểu đồ!")
        elif "xóa dữ liệu" in msg_content or "clear data" in msg_content:
            clear_transactions()
            await message.author.send("Dữ liệu đã được xóa!")
    await bot.process_commands(message)

# Ví dụ sử dụng
if __name__ == "__main__":
    bot.run(TOKEN)
