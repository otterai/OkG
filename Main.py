import asyncio
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode, ChatMemberStatus
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import ClientSession

API_TOKEN = "8097633783:AAGYNCb5AxDP1lmvcnKYNIigIKMhvvAA91k"
ADMIN_ID = 7387793694
CHANNEL = "@PythonBotz"

bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# Dummy DB (replace with MongoDB or any DB)
users_db = {}
reports_db = {}
spam_attempts = {}

@dp.message(F.text == "/start")
async def start_command(message: types.Message):
    user_id = message.from_user.id
    if user_id not in users_db:
        users_db[user_id] = {
            "name": message.from_user.first_name or "NoName",
            "username": message.from_user.username or "NoUsername"
        }
        await bot.send_message(
            ADMIN_ID,
            f"🆕 New user:\n• Name: {message.from_user.first_name}\n"
            f"• Username: @{message.from_user.username}\n• ID: <code>{user_id}</code>"
        )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Update", url="https://t.me/PythonBotz"),
         InlineKeyboardButton(text="Support", url="https://t.me/offchats")]
    ])

    await message.answer(
        f"<b>Welcome {message.from_user.first_name}!</b>\n\n"
        "<b>Time to Clean Your Feed!</b>\n"
        "<i>Fake accounts, hate pages, bots — all gone.\n"
        "Send any IG username, and get a solid report guide instantly!\n"
        "Use /meth To Generate Methods</i>\n\n"
        '<b><blockquote>Powered by <a href="https://t.me/+V6ZWf2k9vV1kZmI1">@PythonBotz</a>\n'
        "Built for the real ones.</blockquote></b>",
        reply_markup=keyboard,
        disable_web_page_preview=True
    )

@dp.message(F.text == "/help")
async def help_command(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Support", url="https://t.me/offchats")]
    ])
    await message.answer("<b>Available Commands:</b>\n\n/start - Start the bot\n/meth - Analyze Instagram\n/help - Show help", reply_markup=keyboard)

@dp.message(F.text == "/meth")
async def meth_command(message: types.Message):
    user_id = message.from_user.id
    try:
        member = await bot.get_chat_member(CHANNEL, user_id)
        if member.status in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED]:
            raise Exception("Not subscribed")
    except:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Join Channel", url=f"https://t.me/{CHANNEL.strip('@')}")],
            [InlineKeyboardButton(text="✅ I Joined", callback_data="check_fsub")]
        ])
        return await message.answer(
            "<u><blockquote>Access Denied</blockquote></u>\n\n"
            "<i>This command is for channel members only!</i>",
            reply_markup=keyboard
        )

    await message.answer("<b>Please Send Your Target Username Without @</b>")
    await dp.storage.set_data(user=message.from_user.id, data={"state": "waiting_username"})

@dp.message()
async def handle_username(message: types.Message):
    user_id = message.from_user.id
    data = await dp.storage.get_data(user=user_id)
    if data.get("state") != "waiting_username":
        return

    # Anti-Spam Mechanism
    if user_id in spam_attempts:
        spam_attempts[user_id] += 1
    else:
        spam_attempts[user_id] = 1

    if spam_attempts[user_id] > 5:
        await message.reply("❌ You are sending too many messages. Please wait a while before trying again.")
        return

    username = message.text.strip().lstrip("@")
    await dp.storage.set_data(user=user_id, data={})  # reset state

    async with ClientSession() as session:
        try:
            async with session.get(f"https://ig-info-drsudo.vercel.app/api/ig?user={username}") as resp:
                ig_data = await resp.json()
        except:
            return await message.answer("Error fetching data. Try again.")

    # Calculate Ban Chances
    ban_chances = random.randint(0, 100)
    ban_message = f"⚠️ Ban chances: {ban_chances}%"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Yes ✅", callback_data=f"confirm_yes_{username}"),
            InlineKeyboardButton(text="No ❌", callback_data="confirm_no")
        ]
    ])
    await message.answer(
        f"<b>Is this the correct user?</b>\n\n"
        f"• <b>Username:</b> {ig_data['username']}\n"
        f"• <b>Nickname:</b> {ig_data.get('nickname', 'N/A')}\n"
        f"• <b>Followers:</b> {ig_data['followers']}\n"
        f"• <b>Following:</b> {ig_data['following']}\n"
        f"• <b>Created At:</b> {ig_data['account_created']}\n\n"
        f"{ban_message}",
        reply_markup=keyboard
    )

@dp.callback_query(F.data.startswith("confirm_yes_"))
async def confirm_username(callback: types.CallbackQuery):
    username = callback.data.replace("confirm_yes_", "")
    await callback.message.delete()

    loading_msg = await callback.message.answer("<b>Generating method... Please wait.</b>")

    # fake progress bar
    for i in range(10, 101, 10):
        bar = '▓' * (i // 10) + '░' * (10 - i // 10)
        await loading_msg.edit_text(f"<b>🔍 Scanning Profile... {i}%</b>\n<pre>{bar}</pre>")
        await asyncio.sleep(0.1)

    if username in reports_db:
        report_lines = [f"➥ {cat}" for cat in reports_db[username]]
    else:
        categories = [
            'Nudity¹', 'Nudity²', 'Nudity³', 'Hate', 'Scam', 'Terrorism',
            'Vio¹', 'Vio²', 'Sale Illegal [Drugs]', 'Firearms',
            'Self_Injury', 'Spam'
        ]
        picked = random.sample(categories, random.randint(2, 5))
        reports_db[username] = picked
        report_lines = [f"➥ {random.randint(1, 5)}x {cat}" for cat in picked]

    final_text = (
        f"<i>Username : @{username}</i>\n\n"
        f"<b>Suggested Reports:</b>\n\n<pre>{chr(10).join(report_lines)}</pre>\n\n"
        "<blockquote>⚠️ <b>Note:</b> <i>This method is based on available data and may not be fully accurate.</i></blockquote>"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="ᴜᴘᴅᴀᴛᴇ", url="https://t.me/PythonBotz"),
            InlineKeyboardButton(text="ᴅᴇᴠʟᴏᴘᴇʀ", url="https://t.me/existable")
        ],
        [InlineKeyboardButton(text="ᴛᴀʀɢᴇᴛ ᴘʀᴏғɪʟᴇ", url=f"https://instagram.com/{username}")]
    ])

    await loading_msg.edit_text(final_text, reply_markup=keyboard)

@dp.callback_query(F.data == "confirm_no")
async def retry_username(callback: types.CallbackQuery):
    await dp.storage.set_data(user=callback.from_user.id, data={"state": "waiting_username"})
    await callback.message.edit_text("<b>Okay, Try again.</b>")

@dp.callback_query(F.data == "check_fsub")
async def check_subscription(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    try:
        member = await bot.get_chat_member(CHANNEL, user_id)
        if member.status in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED]:
            return await callback.answer("Still not joined.", show_alert=True)
        await callback.answer("Thanks! Use /meth")
    except:
        await callback.answer("Error checking.", show_alert=True)

@dp.message(F.text == "/broadcast")
async def broadcast_command(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.reply("❌ You are not authorized to use this.")

    await dp.storage.set_data(user=message.from_user.id, data={"state": "waiting_broadcast"})
    await message.reply("📢 Please send the message you want to broadcast to all users.")

@dp.message()
async def handle_broadcast(message: types.Message):
    data = await dp.storage.get_data(user=message.from_user.id)
    if data.get("state") != "waiting_broadcast":
        return

    await dp.storage.set_data(user=message.from_user.id, data={})  # reset state
    text = message.text

    sent = 0
    failed = 0
    for user_id in users_db.keys():
        try:
            await bot.send_message(user_id, text)
            sent += 1
            await asyncio.sleep(0.05)  # slow down a bit to avoid flood
        except:
            failed += 1

    await message.reply(f"✅ Broadcast complete!\n\n✅ Sent: {sent}\n❌ Failed: {failed}")

if __name__ == "__main__":
    import logging
    from aiogram import Router
    from aiogram.fsm.storage.memory import MemoryStorage
    dp.storage = MemoryStorage()
    dp.include_router(Router())
    logging.basicConfig(level=logging.INFO)
    asyncio.run(dp.start_polling(bot))
    
