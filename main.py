#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import re
import random
import string
from datetime import datetime
from io import BytesIO
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import google.generativeai as genai
import base64

print("🚀 بوت Gemini AI يعمل على Render!")

# إعداد المفاتيح
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
    print("❌ تأكد من تعيين المفاتيح في Environment Variables")
    sys.exit(1)

# إعداد Gemini AI
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# إعداد البوت
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# وظائف مساعدة
def extract_text_with_gemini(image_url):
    """استخراج النصوص باستخدام Gemini AI"""
    try:
        # تحميل الصورة
        response = requests.get(image_url)
        image_bytes = response.content
        
        # تحويل الصورة إلى base64
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # استخراج النصوص
        prompt = """
        استخرج جميع النصوص من هذه الصورة.
        أجب بالتنسيق التالي:
        
        النصوص العربية:
        [النصوص هنا]
        
        النصوص الإنجليزية:
        [النصوص هنا]
        
        اسم الشخص:
        [الاسم هنا]
        
        إذا لم تجد، اكتب "لا يوجد"
        """
        
        response = model.generate_content([
            prompt,
            {"mime_type": "image/jpeg", "data": image_b64}
        ])
        
        # تحليل الاستجابة
        result = {"arabic": [], "english": [], "name": ""}
        current_section = None
        
        for line in response.text.split('\n'):
            line = line.strip()
            
            if line.startswith("النصوص العربية:"):
                current_section = "arabic"
            elif line.startswith("النصوص الإنجليزية:"):
                current_section = "english"
            elif line.startswith("اسم الشخص:"):
                current_section = "name"
            elif line and current_section:
                if current_section == "name":
                    result["name"] = line
                elif line != "لا يوجد":
                    result[current_section].append(line)
        
        return result
        
    except Exception as e:
        print(f"خطأ في Gemini: {e}")
        return {"arabic": [], "english": [], "name": ""}

def create_email(name):
    """إنشاء بريد إلكتروني"""
    if not name:
        name = "user"
    
    # تنظيف الاسم
    name_clean = re.sub(r'[^\w\s]', '', str(name))
    name_clean = name_clean.strip().replace(' ', '.').lower()[:15]
    
    if len(name_clean) < 3:
        name_clean = f"user{random.randint(1000, 9999)}"
    
    return f"{name_clean}@idcard.com"

def generate_password():
    """إنشاء كلمة مرور"""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(12))

def create_text_file(arabic, english, email, password, name=""):
    """إنشاء ملف نصي"""
    content = "=" * 50 + "\n"
    content += "📄 المعلومات المستخرجة\n"
    content += "=" * 50 + "\n\n"
    
    if name:
        content += f"👤 الاسم: {name}\n\n"
    
    content += "العربية:\n"
    content += "-" * 30 + "\n"
    for i, text in enumerate(arabic[:10], 1):
        content += f"{i}. {text[:100]}\n"
    
    content += "\nالإنجليزية:\n"
    content += "-" * 30 + "\n"
    for i, text in enumerate(english[:10], 1):
        content += f"{i}. {text[:100]}\n"
    
    content += "\n" + "=" * 50 + "\n\n"
    content += f"📧 البريد: {email}\n"
    content += f"🔐 كلمة المرور: {password}\n"
    content += f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    content += "=" * 50
    
    return content

# معالجات البوت
@bot.message_handler(commands=['start'])
def start(message):
    welcome = """
🌟 أهلاً! بوت استخراج النصوص بالذكاء الاصطناعي

📸 أرسل صورة البطاقة أو الجواز وسأقوم تلقائياً بـ:
1. استخراج النصوص العربية والإنجليزية
2. إنشاء بريد إلكتروني
3. إنشاء كلمة مرور قوية
4. إرسال ملف بالنتائج

🚀 جرب الآن!
"""
    bot.reply_to(message, welcome)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        msg = bot.reply_to(message, "📥 جاري المعالجة...")
        
        # تحميل الصورة
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        file_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_info.file_path}"
        
        # استخراج النصوص
        result = extract_text_with_gemini(file_url)
        
        if not result["arabic"] and not result["english"]:
            bot.edit_message_text("⚠️ لم أتمكن من استخراج نصوص", 
                                chat_id=message.chat.id, 
                                message_id=msg.message_id)
            return
        
        # إنشاء بيانات
        name = result["name"] or "مستخدم"
        email = create_email(name)
        password = generate_password()
        
        # إنشاء ملف
        file_content = create_text_file(
            result["arabic"], 
            result["english"], 
            email, 
            password,
            name
        )
        
        filename = f"info_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        file_io = BytesIO(file_content.encode('utf-8'))
        file_io.name = filename
        
        # إرسال النتائج
        bot.send_document(
            message.chat.id,
            file_io,
            caption=f"✅ تم!\n📧 {email}\n🔐 {password}"
        )
        
        bot.delete_message(message.chat.id, msg.message_id)
        
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ: {str(e)[:100]}")

# تشغيل البوت
print("🤖 البوت جاهز للتشغيل!")
bot.polling()
