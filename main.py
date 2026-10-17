import logging
import json
import os
from io import BytesIO
from PIL import Image
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Admin ရဲ့ Telegram User ID
ADMIN_ID = 8012437507

# User စာရင်းမှတ်မည့် JSON ဖိုင်
USERS_FILE = "users.json"

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

def load_users():
    """User စာရင်း ဖတ်ယူခြင်း"""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()

def save_users(users):
    """User အသစ်ကို JSON ဖိုင်ထဲ သိမ်းဆည်းခြင်း"""
    try:
        with open(USERS_FILE, "w") as f:
            json.dump(list(users), f)
    except Exception as e:
        logging.error(f"Error saving users: {e}")

def track_user(user_id):
    """User ID ကို စစ်ဆေးပြီး မှတ်တမ်းတင်ခြင်း"""
    users = load_users()
    if user_id not in users:
        users.add(user_id)
        save_users(users)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start command လက်ခံခြင်း"""
    user_id = update.effective_user.id
    track_user(user_id)
    
    context.user_data["images"] = []
    
    await update.message.reply_text(
        "မင်္ဂလာပါ! 📸\n\n"
        "PDF ပြောင်းလိုသော ဓာတ်ပုံများကို တစ်ပုံချင်းစီ ပို့ပေးပါ။\n"
        "ပုံများ ပို့ပြီးပါက PDF ထုတ်ယူရန် /convert ဟု ရိုက်ပို့ပါ ခင်ဗျာ။"
    )

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ဓာတ်ပုံများ လက်ခံခြင်း"""
    user_id = update.effective_user.id
    track_user(user_id)
    
    if "images" not in context.user_data:
        context.user_data["images"] = []

    photo_file = await update.message.photo[-1].get_file()
    image_bytes = await photo_file.download_as_bytearray()
    
    image = Image.open(BytesIO(image_bytes))
    if image.mode != "RGB":
        image = image.convert("RGB")
        
    context.user_data["images"].append(image)
    
    count = len(context.user_data["images"])
    await update.message.reply_text(f"ဓာတ်ပုံ ({count}) ပုံ လက်ခံရရှိပါပြီ။ နောက်ထပ်ပုံများ ဆက်ပို့နိုင်သလို PDF ပြောင်းရန် /convert ကို နှိပ်ပါ ခင်ဗျာ။")

async def convert_to_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """PDF အဖြစ် ပြောင်းလဲပေးခြင်း"""
    user_id = update.effective_user.id
    track_user(user_id)
    
    images = context.user_data.get("images", [])
    
    if not images:
        await update.message.reply_text("ကျေးဇူးပြု၍ PDF ပြောင်းလိုသော ဓာတ်ပုံများကို အရင် ပို့ပေးပါ ခင်ဗျာ။")
        return

    await update.message.reply_text("PDF သို့ ပြောင်းလဲနေပါသည်... ခဏစောင့်ပါ ခင်ဗျာ။")
    
    pdf_bytes = BytesIO()
    first_image = images[0]
    rest_images = images[1:]
    
    first_image.save(
        pdf_bytes,
        format="PDF",
        save_all=True,
        append_images=rest_images
    )
    pdf_bytes.seek(0)
    
    await update.message.reply_document(
        document=pdf_bytes,
        filename="Converted_Document.pdf",
        caption="သင့်ရဲ့ PDF ဖိုင် ရရှိပါပြီ ခင်ဗျာ! ✨"
    )
    
    context.user_data["images"] = []

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin တစ်ယောက်တည်း စုစုပေါင်း User အရေအတွက် ကြည့်ရန် Command"""
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        users = load_users()
        await update.message.reply_text(f"📊 **Bot သုံးစွဲသူ စာရင်းအချက်အလက်**\n\nစုစုပေါင်း သုံးစွဲသူ: **{len(users)}** ယောက် ရှိပါသည်။")
    else:
        await update.message.reply_text("ဒီ command ကို Admin ပဲ သုံးခွင့်ရှိပါတယ် ခင်ဗျာ။")

if __name__ == "__main__":
    TOKEN = os.getenv("BOT_TOKEN")
    
    if not TOKEN:
        raise ValueError("BOT_TOKEN မတွေ့ပါ။ Render ရဲ့ Environment Variables ထဲမှာ စစ်ဆေးပေးပါ ခင်ဗျာ။")
        
    app = ApplicationBuilder().token(TOKEN).connect_timeout(30).read_timeout(30).write_timeout(30).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("convert", convert_to_pdf))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(MessageHandler(filters.PHOTO, handle_image))

    app.run_polling()
