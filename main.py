import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from PIL import Image

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("BOT_TOKEN")

USER_IMAGES = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "မင်္ဂလာပါ! ကျွန်တော်က File Converter Bot ပါ။\n"
        "ကျေးဇူးပြု၍ PDF ပြောင်းလိုသော ပုံများကို တစ်ပုံချင်း (သို့မဟုတ်) အများပြား ပို့ပေးပါ။ "
        "ပြီးလျှင် /done လို့ ရိုက်ပို့လိုက်ရင် PDF ဖိုင်အဖြစ် ပြန်ထုတ်ပေးပါမယ်။"
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    photo_file = await update.message.photo[-1].get_file()
    
    file_path = f"{user_id}_{len(USER_IMAGES.get(user_id, []))}.jpg"
    await photo_file.download_to_drive(file_path)
    
    if user_id not in USER_IMAGES:
        USER_IMAGES[user_id] = []
    USER_IMAGES[user_id].append(file_path)
    
    await update.message.reply_text(f"ပုံ လက်ခံရရှိပါပြီ။ စုစုပေါင်း ပုံအရေအတွက်: {len(USER_IMAGES[user_id])}\nဆက်ပို့ရန် (သို့မဟုတ်) ပြီးရင် /done လို့ ရိုက်ပါ။")

async def generate_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in USER_IMAGES or not USER_IMAGES[user_id]:
        await update.message.reply_text("ကျေးဇူးပြု၍ ပထမဆုံး ပုံများ ပို့ပေးပါ။")
        return

    images = USER_IMAGES[user_id]
    pdf_path = f"{user_id}_converted.pdf"

    try:
        image_objects = [Image.open(img).convert('RGB') for img in images]
        image_objects[0].save(pdf_path, save_all=True, append_images=image_objects[1:])
        
        with open(pdf_path, 'rb') as pdf_file:
            await update.message.reply_document(document=pdf_file, caption="သင့်ရဲ့ PDF ဖိုင် ရပါပြီ!")
            
    except Exception as e:
        logger.error(f"PDF conversion error: {e}")
        await update.message.reply_text("PDF ပြောင်းရာတွင် အမှားအယွင်း ရှိသွားပါသည်။")
    finally:
        for img in images:
            if os.path.exists(img):
                os.remove(img)
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
        USER_IMAGES[user_id] = []

def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("done", generate_pdf))
    application.add_handler(MessageHandler(filters.PHOTO & ~filters.COMMAND, handle_photo))

    application.run_polling()

if __name__ == "__main__":
    main()
