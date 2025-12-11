#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import re
import random
import string
from datetime import datetime
from io import BytesIO
import json

print("🚀 جاري تشغيل بوت استخراج النصوص...")

# ============= تثبيت المكتبات تلقائياً =============
def install_requirements():
    """تثبيت المتطلبات تلقائياً"""
    packages = [
        'pyTelegramBotAPI',
        'requests',
        'Pillow',
        'google-generativeai'  # لحلول Gemini AI
    ]
    
    print("📦 جاري تثبيت المكتبات...")
    for package in packages:
        try:
            __import__(package.replace('-', '_').replace('pyTelegramBotAPI', 'telebot'))
            print(f"✅ {package} مثبت")
        except ImportError:
            print(f"⬇️ جاري تثبيت {package}...")
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    
    print("✅ جميع المكتبات مثبتة!\n")

# استدعاء تثبيت المكتبات
install_requirements()

# ============= استيراد المكتبات بعد التثبيت =============
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests

# ============= إعداد البوت =============
TOKEN = os.environ.get('TELEGRAM_TOKEN', '')
if not TOKEN:
    print("❌ لم يتم تعيين توكن البوت!")
    print("🔑 أضف TELEGRAM_TOKEN في Environment Variables")
    sys.exit(1)

bot = telebot.TeleBot(TOKEN)

# ============= وظائف مساعدة =============
def generate_email(name):
    """إنشاء بريد إلكتروني من الاسم"""
    if not name:
        name = "user"
    
    name_clean = re.sub(r'[^\w\s]', '', str(name))
    name_clean = name_clean.strip().replace(' ', '.').lower()[:15]
    
    if len(name_clean) < 3:
        name_clean = f"user{random.randint(1000, 9999)}"
    
    domains = ["idcard.com", "official.me", "passport.co"]
    domain = random.choice(domains)
    
    return f"{name_clean}@{domain}"

def generate_password():
    """إنشاء كلمة مرور قوية"""
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choice(chars) for _ in range(12))

def create_text_file(arabic_texts, english_texts, email, password):
    """إنشاء ملف نصي"""
    content = "=" * 50 + "\n"
    content += "📄 المعلومات المستخرجة\n"
    content += "=" * 50 + "\n\n"
    
    content += "🔤 النصوص العربية:\n"
    content += "-" * 30 + "\n"
    if arabic_texts:
        for i, text in enumerate(arabic_texts, 1):
            content += f"{i:02d}. {text}\n"
    else:
        content += "❌ لم يتم العثور على نصوص عربية\n"
    
    content += "\n" + "=" * 50 + "\n\n"
    
    content += "🔤 النصوص الإنجليزية:\n"
    content += "-" * 30 + "\n"
    if english_texts:
        for i, text in enumerate(english_texts, 1):
            content += f"{i:02d}. {text}\n"
    else:
        content += "❌ لم يتم العثور على نصوص إنجليزية\n"
    
    content += "\n" + "=" * 50 + "\n\n"
    
    content += "📧 بيانات الدخول المنشأة:\n"
    content += "-" * 40 + "\n"
    content += f"📧 البريد الإلكتروني: {email}\n"
    content += f"🔐 كلمة المرور: {password}\n\n"
    
    content += "📅 التاريخ: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n"
    content += "=" * 50 + "\n"
    
    return content

# ============= معالجات البوت =============
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_msg = f"""
🌟 أهلاً {message.from_user.first_name}!

🤖 **بوت استخراج النصوص من البطاقة والجواز**

📸 **كيف يعمل:**
1. أرسل صورة البطاقة أو الجواز
2. سأقوم باستخراج النصوص العربية والإنجليزية
3. سأنشئ لك:
   - 📧 بريد إلكتروني
   - 🔐 كلمة مرور قوية
   - 📄 ملف نصي بالنتائج

⚡ **جرب الآن:** أرسل صورة!
"""
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("📸 أرسل صورة الآن", callback_data="send_photo")
    )
    
    bot.reply_to(message, welcome_msg, reply_markup=keyboard, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data == "send_photo")
def ask_for_photo(call):
    bot.answer_callback_query(call.id, "جاهز لاستقبال الصورة")
    bot.send_message(
        call.message.chat.id,
        "📸 الرجاء إرسال صورة البطاقة أو الجواز\n\n"
        "💡 **للحصول على أفضل نتيجة:**\n"
        "• التقط الصورة في إضاءة جيدة\n"
        "• اجعل النصوص واضحة\n"
        "• صور الوثيقة بشكل مستقيم"
    )

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        # إعلام المستخدم
        msg = bot.reply_to(message, "📥 جاري تحميل الصورة...")
        
        # تحميل الصورة
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"
        
        response = requests.get(file_url)
        if response.status_code != 200:
            bot.edit_message_text("❌ فشل تحميل الصورة", 
                                chat_id=message.chat.id, 
                                message_id=msg.message_id)
            return
        
        # تحديث الرسالة
        bot.edit_message_text("⚡ جاري معالجة الصورة...",
                            chat_id=message.chat.id,
                            message_id=msg.message_id)
        
        # محاكاة استخراج النصوص (ستحتاج لتعديل هذا الجزء)
        # هنا يمكنك إضافة OCR حقيقي أو Gemini AI
        
        # بيانات وهمية للاختبار
        arabic_texts = [
            "بطاقة هوية وطنية",
            "الاسم: أحمد محمد",
            "رقم الهوية: 1234567890",
            "تاريخ الميلاد: 01/01/1990"
        ]
        
        english_texts = [
            "National ID Card",
            "Name: Ahmed Mohamed",
            "ID Number: 1234567890",
            "Date of Birth: 01/01/1990"
        ]
        
        # إنشاء بيانات
        name = message.from_user.first_name or "مستخدم"
        email = generate_email(name)
        password = generate_password()
        
        # إنشاء الملف
        bot.edit_message_text("📝 جاري إنشاء الملف...",
                            chat_id=message.chat.id,
                            message_id=msg.message_id)
        
        file_content = create_text_file(arabic_texts, english_texts, email, password)
        filename = f"معلومات_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        # إرسال الملف
        file_io = BytesIO(file_content.encode('utf-8'))
        file_io.name = filename
        
        bot.send_document(
            message.chat.id,
            file_io,
            caption=f"✅ تم!\n📧 {email}\n🔐 {password}"
        )
        
        bot.delete_message(message.chat.id, msg.message_id)
        
        # إرسال ملخص
        summary = f"""
📋 **ملخص سريع:**

**📧 البريد الإلكتروني:** `{email}`
**🔐 كلمة المرور:** `{password}`

⚠️ **احفظ هذه البيانات في مكان آمن!**
"""
        
        bot.send_message(
            message.chat.id,
            summary,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ: {str(e)[:100]}")

# ============= تشغيل البوت =============
print("\n" + "="*50)
print("🤖 البوت يعمل بنجاح!")
print("="*50)

try:
    bot_info = bot.get_me()
    print(f"✅ البوت: {bot_info.first_name}")
    print(f"🆔 المعرف: @{bot_info.username}")
    print("📱 اذهب إلى تيليجرام وأرسل /start")
    
    bot.polling(none_stop=True)
    
except Exception as e:
    print(f"❌ خطأ في تشغيل البوت: {e}")
