import os
import asyncio
from telethon import TelegramClient, events, functions, types

# ===== إعدادات البوت =====
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ضع هنا الايدي الخاص بالمجموعة والقناة وحسابك
GROUP_ID = -1001234567890   # ايدي المجموعة
CHANNEL_ID = -1009876543210 # ايدي القناة
TEST_USER_ID = 111111111    # ايدي حسابك لاختبار البوت

client = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# القوائم
pending_users = {}    # الأعضاء المعلقين على الانضمام للقناة
restricted_users = {} # الأعضاء المقيدين حاليًا

# ===== مراقبة الرسائل في المجموعة المحددة فقط =====
@client.on(events.NewMessage(chats=GROUP_ID))
async def restrict_member(event):
    sender = await event.get_sender()
    user_id = sender.id
    chat_id = event.chat_id

    # فقط للأعضاء غير المختبرين لتجنب تقييد نفسك
    if user_id == TEST_USER_ID:
        return

    if user_id in pending_users:
        return

    # تقييد العضو فورًا
    await client.edit_permissions(chat_id, user_id, send_messages=False)
    restricted_users[user_id] = chat_id
    pending_users[user_id] = chat_id

    # إرسال رسالة التحذير
    await event.reply(
        f'عزيزي @{sender.username if sender.username else sender.first_name} '
        f'يجب عليك الانضمام في القناة ثم تابع كلامك معنا نحن بانتظارك {CHANNEL_ID}'
    )

# ===== فحص القناة كل 10 ثواني =====
async def check_channel():
    while True:
        to_remove = []
        for user_id, chat_id in pending_users.items():
            try:
                participant = await client(functions.channels.GetParticipantRequest(
                    channel=CHANNEL_ID,
                    participant=user_id
                ))
                if isinstance(participant.participant, (types.ChannelParticipant, types.ChannelParticipantSelf)):
                    # فتح إرسال الرسائل
                    await client.edit_permissions(chat_id, user_id, send_messages=True)
                    # إزالة العضو من القوائم
                    to_remove.append(user_id)
                    if user_id in restricted_users:
                        restricted_users.pop(user_id)
            except:
                pass
        for user_id in to_remove:
            pending_users.pop(user_id)
        await asyncio.sleep(10)

# ===== أمر /start =====
@client.on(events.NewMessage(pattern="^/start$"))
async def start_command(event):
    await event.respond("✅ البوت يعمل بنجاح على النسخة التجريبية!")

# ===== أمر /pending =====
@client.on(events.NewMessage(pattern="/pending"))
async def show_pending(event):
    msg = "📋 قائمة الأعضاء المعلقين:\n"
    if not pending_users:
        await event.respond("لا يوجد أعضاء معلقين حاليًا ✅")
        return

    for user_id in pending_users:
        try:
            user = await client.get_entity(user_id)
            username = f"@{user.username}" if user.username else user.first_name
            msg += f"- {username} (ID: {user_id})\n"
        except:
            msg += f"- Unknown (ID: {user_id})\n"
    await event.respond(msg)

# ===== أمر /restricted =====
@client.on(events.NewMessage(pattern="/restricted"))
async def show_restricted(event):
    msg = "📋 قائمة الأعضاء المقيدين:\n"
    if not restricted_users:
        await event.respond("لا يوجد أعضاء مقيدين حاليًا ✅")
        return

    for user_id in restricted_users:
        try:
            user = await client.get_entity(user_id)
            username = f"@{user.username}" if user.username else user.first_name
            msg += f"- {username} (ID: {user_id})\n"
        except:
            msg += f"- Unknown (ID: {user_id})\n"
    await event.respond(msg)

# ===== تشغيل البوت على Heroku =====
async def main():
    asyncio.create_task(check_channel())
    print("🤖 Bot is running on test mode...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    client.start(bot_token=BOT_TOKEN)
    asyncio.run(main())