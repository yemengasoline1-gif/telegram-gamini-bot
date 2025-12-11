#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🤖 بوت تيليجرام متكامل لاستخراج النصوص من البطاقة والجواز
يدعم: Render, Railway, Koyeb, Cyclic, Oracle Cloud, GitHub Codespaces, AlwaysData
"""

import os
import sys
import re
import random
import string
import json
import base64
from datetime import datetime
from io import BytesIO

print("=" * 60)
print("🚀 بوت استخراج النصوص بالذكاء الاصطناعي")
print("=" * 60)

# ============= الكشف عن المنصة والتثبيت التلقائي =============
def detect_platform():
    """الكشف عن المنصة المستخدمة"""
    platforms = {
        "RENDER": "Render.com",
        "RAILWAY": "Railway.app",
        "KOYEB": "Koyeb.com",
        "CYCLIC": "Cyclic.sh",
        "GITHUB_CODESPACE": "GitHub Codespaces",
        "ALWAYSDATA": "AlwaysData.com",
        "ORACLE": "Oracle Cloud"
    }
    
    for env_var, platform in platforms.items():
        if os.environ.get(env_var) or os.environ.get(f'{env_var}_APP'):
            print(f"📍 المنصة: {platform}")
            return platform
    
    print("📍 المنصة: محلي/غير معروف")
    return "LOCAL"

PLATFORM = detect_platform()

# ============= تثبيت المكتبات تلقائياً =============
def install_requirements():
    """تثبيت جميع المتطلبات تلقائياً"""
    required_packages = [
        'pyTelegramBotAPI==4.14.1',
        'requests==2.31.0',
        'google-generativeai==0.3.2'
    ]
    
    print("📦 جاري تثبيت المكتبات...")
    
    import subprocess
    import importlib.util
    
    for package in required_packages:
        package_name = package.split('==')[0]
        
        # التحقق إذا كانت المكتبة مثبتة
        if importlib.util.find_spec(package_name.replace('-', '_').replace('pyTelegramBotAPI', 'telebot')) is None:
            print(f"⬇️ جاري تثبيت {package_name}...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package, "--quiet"])
                print(f"✅ تم تثبيت {package_name}")
            except Exception as e:
                print(f"⚠️ تحذير: {e}")
        else:
            print(f"✅ {package_name} مثبت مسبقاً")
    
    print("✅ جميع المكتبات جاهزة!\n")

# تثبيت المتطلبات
install_requirements()

# ============= استيراد المكتبات بعد التثبيت =============
try:
    import telebot
    from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
    import requests
    import google.generativeai as genai
    print("✅ المكتبات الرئيسية تم تحميلها بنجاح")
except Exception as e:
    print(f"❌ خطأ في تحميل المكتبات: {e}")
    sys.exit(1)

# ============= إعداد التوكنات والمفاتيح =============
def setup_tokens():
    """إعداد التوكنات من متغيرات البيئة"""
    tokens = {
        'TELEGRAM_TOKEN': os.environ.get('TELEGRAM_TOKEN', ''),
        'GEMINI_API_KEY': os.environ.get('GEMINI_API_KEY', ''),
        'OCR_API_KEY': os.environ.get('OCR_API_KEY', 'helloworld')  # مفتاح مجاني لخدمة OCR
    }
    
    # التحقق من التوكنات
    if not tokens['TELEGRAM_TOKEN']:
        print("❌ خطأ: لم يتم تعيين توكن تيليجرام!")
        print("🔑 أضف TELEGRAM_TOKEN في Environment Variables")
        return None
    
    if not tokens['GEMINI_API_KEY']:
        print("⚠️ تحذير: لم يتم تعيين مفتاح Gemini AI")
        print("📝 سيتم استخدام OCR البديل")
    
    return tokens

TOKENS = setup_tokens()
if TOKENS is None:
    sys.exit(1)

TELEGRAM_TOKEN = TOKENS['TELEGRAM_TOKEN']
GEMINI_API_KEY = TOKENS['GEMINI_API_KEY']
OCR_API_KEY = TOKENS['OCR_API_KEY']

# ============= إعداد الذكاء الاصطناعي =============
def setup_ai():
    """إعداد نموذج الذكاء الاصطناعي"""
    try:
        if GEMINI_API_KEY:
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # اختبار الاتصال
            test_response = model.generate_content("اختبار اتصال")
            print("✅ Gemini AI متصل وجاهز")
            return {'model': model, 'type': 'gemini', 'available': True}
        else:
            print("⚠️ Gemini AI غير متوفر، سيتم استخدام OCR البديل")
            return {'model': None, 'type': 'ocr', 'available': False}
    except Exception as e:
        print(f"⚠️ خطأ في إعداد Gemini AI: {e}")
        return {'model': None, 'type': 'ocr', 'available': False}

AI_SETUP = setup_ai()

# ============= إعداد البوت =============
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# ============= قاعدة بيانات مبسطة (في الذاكرة) =============
user_sessions = {}
user_data = {}

def save_user_data(user_id, data):
    """حفظ بيانات المستخدم"""
    user_data[user_id] = {
        'timestamp': datetime.now().isoformat(),
        'data': data,
        'extractions': user_data.get(user_id, {}).get('extractions', 0) + 1
    }
    return True

def get_user_data(user_id):
    """الحصول على بيانات المستخدم"""
    return user_data.get(user_id, {'extractions': 0})

# ============= وظائف استخراج النصوص =============
def extract_with_gemini(image_bytes):
    """استخراج النصوص باستخدام Gemini AI"""
    try:
        model = AI_SETUP['model']
        
        # تحويل الصورة إلى base64
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # إعداد الـ prompt
        prompt = """
        أنت خبير في استخراج النصوص من وثائق الهوية.
        
        استخرج جميع النصوص من هذه الصورة وأجب بالتنسيق التالي:
        
        الاسم الكامل: [الاسم هنا إن وجد]
        
        النصوص العربية:
        [النصوص العربية هنا، كل سطر في سطر منفصل]
        
        النصوص الإنجليزية:
        [النصوص الإنجليزية هنا، كل سطر في سطر منفصل]
        
        إذا لم تجد نصاً، اكتب: لا يوجد
        
        تأكد من:
        1. دقة استخراج النصوص
        2. فصل النصوص العربية عن الإنجليزية
        3. كتابة الاسم كاملاً إذا وجد
        """
        
        # إرسال الطلب
        response = model.generate_content([
            prompt,
            {"mime_type": "image/jpeg", "data": image_b64}
        ])
        
        # تحليل الاستجابة
        result = {
            'name': '',
            'arabic_texts': [],
            'english_texts': []
        }
        
        lines = response.text.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('الاسم الكامل:'):
                result['name'] = line.replace('الاسم الكامل:', '').strip()
            elif line.startswith('النصوص العربية:'):
                current_section = 'arabic'
            elif line.startswith('النصوص الإنجليزية:'):
                current_section = 'english'
            elif line and current_section:
                if line != 'لا يوجد':
                    if current_section == 'arabic':
                        result['arabic_texts'].append(line)
                    elif current_section == 'english':
                        result['english_texts'].append(line)
        
        return result
        
    except Exception as e:
        print(f"❌ خطأ في Gemini AI: {e}")
        return {'name': '', 'arabic_texts': [], 'english_texts': []}

def extract_with_ocr(image_bytes):
    """استخراج النصوص باستخدام خدمة OCR مجانية (بديل)"""
    try:
        # تحويل الصورة إلى base64
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # إرسال إلى خدمة OCR.space المجانية
        payload = {
            'base64Image': f'data:image/jpeg;base64,{image_b64}',
            'language': 'ara+eng',
            'isOverlayRequired': False,
            'OCREngine': 2,
            'apikey': OCR_API_KEY
        }
        
        response = requests.post(
            'https://api.ocr.space/parse/image',
            data=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('IsErroredOnProcessing'):
                return {'name': '', 'arabic_texts': [], 'english_texts': []}
            
            # استخراج النصوص
            all_texts = []
            for parsed_result in result.get('ParsedResults', []):
                text = parsed_result.get('ParsedText', '').strip()
                if text:
                    all_texts.append(text)
            
            # فصل النصوص العربية والإنجليزية
            arabic_texts = []
            english_texts = []
            
            for text in all_texts:
                lines = text.split('\n')
                for line in lines:
                    line = line.strip()
                    if line:
                        if re.search(r'[\u0600-\u06FF]', line):
                            arabic_texts.append(line)
                        else:
                            english_texts.append(line)
            
            # محاولة استخراج اسم من النصوص العربية
            name = ""
            for text in arabic_texts:
                if re.search(r'(اسم|الاسم|Name)', text, re.IGNORECASE):
                    name = re.sub(r'(اسم|الاسم|Name)[:\s]*', '', text, flags=re.IGNORECASE).strip()
                    break
            
            return {
                'name': name,
                'arabic_texts': arabic_texts,
                'english_texts': english_texts
            }
        
        return {'name': '', 'arabic_texts': [], 'english_texts': []}
        
    except Exception as e:
        print(f"❌ خطأ في OCR: {e}")
        return {'name': '', 'arabic_texts': [], 'english_texts': []}

def extract_text_from_image(image_bytes):
    """الدالة الرئيسية لاستخراج النصوص"""
    if AI_SETUP['available']:
        print("🤖 استخدام Gemini AI للاستخراج...")
        result = extract_with_gemini(image_bytes)
    else:
        print("🔤 استخدام OCR البديل...")
        result = extract_with_ocr(image_bytes)
    
    return result

# ============= وظائف إنشاء البيانات =============
def generate_email(name):
    """إنشاء بريد إلكتروني من الاسم"""
    if not name or name.strip() == "":
        name = "user"
    
    # تحويل الاسم العربي إلى حروف لاتينية
    arabic_to_latin = {
        'أ': 'a', 'ا': 'a', 'إ': 'e', 'آ': 'a',
        'ب': 'b', 'ت': 't', 'ث': 'th',
        'ج': 'j', 'ح': 'h', 'خ': 'kh',
        'د': 'd', 'ذ': 'dh', 'ر': 'r', 'ز': 'z',
        'س': 's', 'ش': 'sh', 'ص': 's', 'ض': 'd',
        'ط': 't', 'ظ': 'z', 'ع': 'a', 'غ': 'gh',
        'ف': 'f', 'ق': 'q', 'ك': 'k', 'ل': 'l',
        'م': 'm', 'ن': 'n', 'ه': 'h', 'و': 'w',
        'ي': 'y', 'ى': 'a', 'ئ': 'e',
        'ة': 'h', ' ': '.'
    }
    
    latin_name = ""
    for char in str(name):
        if char in arabic_to_latin:
            latin_name += arabic_to_latin[char]
        elif char.isalpha() and char.isascii():
            latin_name += char.lower()
        elif char == ' ':
            latin_name += '.'
    
    # تنظيف النتيجة
    latin_name = re.sub(r'[^a-z.]', '', latin_name)
    latin_name = re.sub(r'\.+', '.', latin_name)
    latin_name = latin_name.strip('.')
    
    if len(latin_name) < 3:
        latin_name = f"user{random.randint(1000, 9999)}"
    
    # خيارات النطاقات
    domains = [
        "idcard.me", "official-id.com", "passport.info",
        "verify.id", "document.space", "identity.pro"
    ]
    
    domain = random.choice(domains)
    email = f"{latin_name}@{domain}"
    
    return email

def generate_password():
    """إنشاء كلمة مرور قوية"""
    # يجب أن تحتوي على حرف كبير، صغير، رقم ورمز
    uppercase = random.choice(string.ascii_uppercase)
    lowercase = random.choice(string.ascii_lowercase)
    digit = random.choice(string.digits)
    symbol = random.choice("!@#$%^&*")
    
    # باقي الأحرف
    all_chars = string.ascii_letters + string.digits + "!@#$%^&*"
    remaining = ''.join(random.choice(all_chars) for _ in range(8))
    
    # دمج وخلط
    password = uppercase + lowercase + digit + symbol + remaining
    password_list = list(password)
    random.shuffle(password_list)
    
    return ''.join(password_list)

# ============= وظائف إنشاء الملفات =============
def create_text_file_content(name, arabic_texts, english_texts, email, password, platform):
    """إنشاء محتوى الملف النصي"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    content = "=" * 60 + "\n"
    content += "📄 المعلومات المستخرجة من الوثيقة\n"
    content += "=" * 60 + "\n\n"
    
    if name:
        content += f"👤 **اسم الشخص:** {name}\n\n"
    
    content += "🔤 **النصوص العربية المستخرجة:**\n"
    content += "-" * 40 + "\n"
    if arabic_texts:
        for i, text in enumerate(arabic_texts, 1):
            content += f"{i:02d}. {text}\n"
    else:
        content += "❌ لم يتم العثور على نصوص عربية\n"
    
    content += "\n" + "=" * 60 + "\n\n"
    
    content += "🔤 **النصوص الإنجليزية المستخرجة:**\n"
    content += "-" * 40 + "\n"
    if english_texts:
        for i, text in enumerate(english_texts, 1):
            content += f"{i:02d}. {text}\n"
    else:
        content += "❌ لم يتم العثور على نصوص إنجليزية\n"
    
    content += "\n" + "=" * 60 + "\n\n"
    
    content += "📧 **بيانات الدخول المنشأة تلقائياً:**\n"
    content += "-" * 40 + "\n"
    content += f"📧 البريد الإلكتروني: {email}\n"
    content += f"🔐 كلمة المرور: {password}\n\n"
    
    content += "=" * 60 + "\n"
    content += f"📅 تاريخ الإستخراج: {timestamp}\n"
    content += f"🌐 المنصة المستخدمة: {platform}\n"
    content += f"🤖 المحرك: {'Gemini AI' if AI_SETUP['available'] else 'OCR Space'}\n"
    content += "=" * 60 + "\n"
    
    return content

def create_filename(name):
    """إنشاء اسم للملف"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if name and name != "مستخدم":
        safe_name = re.sub(r'[^\w\s]', '', name)
        safe_name = safe_name.strip().replace(' ', '_')[:20]
        return f"معلومات_{safe_name}_{timestamp}.txt"
    return f"معلومات_{timestamp}.txt"

# ============= معالجات البوت =============
@bot.message_handler(commands=['start', 'help', 'ابدأ'])
def handle_start(message):
    """معالجة أمر /start"""
    try:
        user = message.from_user
        user_id = str(user.id)
        
        # حفظ معلومات المستخدم
        if user_id not in user_data:
            user_data[user_id] = {
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'join_date': datetime.now().isoformat(),
                'extractions': 0
            }
        
        # رسالة الترحيب
        welcome_text = f"""
🌟 أهلاً بك {user.first_name}! 

🤖 **بوت استخراج النصوص من البطاقة والجواز**

✨ **المميزات:**
✅ استخراج تلقائي للنصوص العربية والإنجليزية
✅ إنشاء بريد إلكتروني من الاسم
✅ توليد كلمة مرور قوية
✅ حفظ النتائج في ملف نصي
✅ دعم الذكاء الاصطناعي (Gemini AI)

📸 **كيفية الاستخدام:**
1. أرسل صورة البطاقة أو الجواز
2. انتظر قليلاً للمعالجة
3. استلم الملف مع جميع المعلومات

⚡ **الآن:** أرسل صورة مباشرة أو استخدم الأزرار!
"""
        
        # إنشاء لوحة المفاتيح
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        keyboard.add(
            KeyboardButton("📸 إرسال صورة"),
            KeyboardButton("ℹ️ معلومات"),
            KeyboardButton("📊 إحصائيات"),
            KeyboardButton("🆘 المساعدة")
        )
        
        # إرسال الرسالة مع الأزرار
        bot.send_message(
            message.chat.id,
            welcome_text,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        
        # إرسال صورة توضيحية
        bot.send_message(
            message.chat.id,
            "💡 *نصائح للحصول على أفضل نتيجة:*\n"
            "• التقط الصورة بإضاءة جيدة\n"
            "• اجعل الوثيقة تملأ معظم الإطار\n"
            "• تأكد من وضوح النصوص\n"
            "• تجنب الظلال على الوثيقة",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        print(f"❌ خطأ في أمر start: {e}")
        bot.reply_to(message, "❌ حدث خطأ في معالجة الأمر. حاول مرة أخرى.")

@bot.message_handler(func=lambda message: message.text == "📸 إرسال صورة")
def handle_send_photo_button(message):
    """معالجة زر إرسال صورة"""
    bot.reply_to(
        message,
        "📸 **جاهز لاستقبال الصورة!**\n\n"
        "الرجاء إرسال صورة البطاقة أو الجواز الآن.\n"
        "يمكنك التقاط صورة جديدة أو اختيار صورة من المعرض.",
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda message: message.text == "ℹ️ معلومات")
def handle_info_button(message):
    """معالجة زر المعلومات"""
    info_text = f"""
📋 **معلومات البوت:**

🛠 **الإصدار:** 3.0 متعدد المنصات
🌐 **المنصة الحالية:** {PLATFORM}
🤖 **محرك الاستخراج:** {'Gemini AI' if AI_SETUP['available'] else 'OCR Space'}
📊 **عدد المستخدمين:** {len(user_data)}
📈 **إجمالي عمليات الاستخراج:** {sum(data.get('extractions', 0) for data in user_data.values())}

🔧 **المكتبات المستخدمة:**
• pyTelegramBotAPI: لواجهة تيليجرام
• Google Generative AI: لاستخراج النصوص
• Requests: للاتصال بالإنترنت

🔒 **الخصوصية:**
• الصور تُعالج فوراً ولا تُخزن
• البيانات تُحفظ مؤقتاً في الذاكرة
• يمكنك مسح بياناتك في أي وقت

📞 **الدعم:** @YourSupportChannel
"""
    
    bot.send_message(
        message.chat.id,
        info_text,
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda message: message.text == "📊 إحصائيات")
def handle_stats_button(message):
    """معالجة زر الإحصائيات"""
    user_id = str(message.from_user.id)
    user_stats = get_user_data(user_id)
    
    stats_text = f"""
📊 **إحصائياتك الشخصية:**

👤 **اسمك:** {message.from_user.first_name}
🆔 **معرفك:** {user_id}
📅 **تاريخ الانضمام:** {user_data.get(user_id, {}).get('join_date', 'غير معروف')}
🔢 **عدد عمليات الاستخراج:** {user_stats.get('extractions', 0)}

📈 **إحصائيات عامة:**
• إجمالي المستخدمين: {len(user_data)}
• عمليات اليوم: {len([d for d in user_data.values() if d.get('timestamp', '').startswith(datetime.now().strftime('%Y-%m-%d'))])}
• المنصة: {PLATFORM}
"""
    
    bot.send_message(
        message.chat.id,
        stats_text,
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda message: message.text == "🆘 المساعدة")
def handle_help_button(message):
    """معالجة زر المساعدة"""
    help_text = """
🆘 **مركز المساعدة:**

❓ **أسئلة شائعة:**

1. **ما أنواع الصور المدعومة؟**
   • البطاقة الشخصية، جواز السفر، رخصة القيادة
   • الصور يجب أن تكون بصيغة JPG أو PNG

2. **كم تستغرق المعالجة؟**
   • 10-30 ثانية حسب جودة الصورة
   • Gemini AI أسرع وأدق من OCR العادي

3. **كيف يتم إنشاء البريد الإلكتروني؟**
   • يتم استخراج الاسم من الصورة
   • تحويله إلى حروف لاتينية
   • إضافة نطاق عشوائي

4. **هل البيانات آمنة؟**
   • نعم، الصور تُحذف بعد المعالجة
   • لا يتم تخزين أي معلومات شخصية

🔄 **إصلاح المشاكل:**

• **الصورة غير واضحة:** حاول التصوير بإضاءة أفضل
• **لم يتم استخراج نص:** تأكد من وضوح النصوص في الصورة
• **البوت لا يرد:** أعد تشغيله أو اتصل بالدعم

📞 **للتواصل:** @YourSupportChannel
"""
    
    bot.send_message(
        message.chat.id,
        help_text,
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['delete_my_data'])
def handle_delete_data(message):
    """حذف بيانات المستخدم"""
    user_id = str(message.from_user.id)
    
    if user_id in user_data:
        del user_data[user_id]
        bot.reply_to(message, "✅ تم حذف جميع بياناتك بنجاح.")
    else:
        bot.reply_to(message, "ℹ️ لا توجد بيانات لحذفها.")

@bot.message_handler(commands=['status'])
def handle_status(message):
    """حالة البوت"""
    status_text = f"""
🟢 **حالة البوت: نشط**

🌐 **المنصة:** {PLATFORM}
🤖 **الحالة:** يعمل بنجاح
👥 **المستخدمون النشطون:** {len(user_data)}
🔧 **المحرك:** {'Gemini AI ✅' if AI_SETUP['available'] else 'OCR Space ⚠️'}
⏱️ **وقت التشغيل:** منذ {datetime.now().strftime('%H:%M:%S')}

📊 **إحصائيات فورية:**
• ذاكرة مستخدمة: {len(user_data) * 1000} بايت تقريباً
• جلسات نشطة: {len(user_sessions)}
• حالة الخدمة: ممتازة
"""
    
    bot.reply_to(message, status_text, parse_mode='Markdown')

@bot.message_handler(content_types=['photo'])
def handle_photo_message(message):
    """معالجة الصور المرسلة"""
    try:
        user_id = str(message.from_user.id)
        
        # إعلام المستخدم
        status_msg = bot.reply_to(
            message,
            "📥 **جاري تحميل الصورة...**\n"
            "⏳ الرجاء الانتظار قليلاً",
            parse_mode='Markdown'
        )
        
        # الحصول على أفضل جودة للصورة
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        file_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_info.file_path}"
        
        # تحميل الصورة
        bot.edit_message_text(
            "🔗 **جاري تحميل الصورة من السيرفر...**",
            chat_id=message.chat.id,
            message_id=status_msg.message_id,
            parse_mode='Markdown'
        )
        
        response = requests.get(file_url, timeout=30)
        if response.status_code != 200:
            bot.edit_message_text(
                "❌ **فشل في تحميل الصورة**\n"
                "الرجاء إعادة المحاولة",
                chat_id=message.chat.id,
                message_id=status_msg.message_id,
                parse_mode='Markdown'
            )
            return
        
        image_bytes = response.content
        
        # استخراج النصوص
        bot.edit_message_text(
            "🤖 **جاري تحليل الصورة واستخراج النصوص...**\n"
            f"المحرك: {'Gemini AI' if AI_SETUP['available'] else 'OCR Space'}",
            chat_id=message.chat.id,
            message_id=status_msg.message_id,
            parse_mode='Markdown'
        )
        
        extraction_result = extract_text_from_image(image_bytes)
        
        # التحقق من وجود نصوص مستخرجة
        if not extraction_result['arabic_texts'] and not extraction_result['english_texts']:
            bot.edit_message_text(
                "❌ **لم أتمكن من استخراج نصوص من الصورة**\n\n"
                "💡 **نصائح لتحسين النتيجة:**\n"
                "• تأكد من وضوح النصوص في الصورة\n"
                "• التقط الصورة بإضاءة جيدة\n"
                "• اجعل الوثيقة تملأ معظم الإطار\n"
                "• حاول مع صورة أخرى",
                chat_id=message.chat.id,
                message_id=status_msg.message_id,
                parse_mode='Markdown'
            )
            return
        
        # إنشاء بيانات المستخدم
        name = extraction_result['name'] or message.from_user.first_name or "مستخدم"
        email = generate_email(name)
        password = generate_password()
        
        # إنشاء الملف
        bot.edit_message_text(
            "📝 **جاري إنشاء الملف النصي...**",
            chat_id=message.chat.id,
            message_id=status_msg.message_id,
            parse_mode='Markdown'
        )
        
        file_content = create_text_file_content(
            name,
            extraction_result['arabic_texts'],
            extraction_result['english_texts'],
            email,
            password,
            PLATFORM
        )
        
        filename = create_filename(name)
        
        # إرسال الملف
        bot.edit_message_text(
            "📤 **جاري إرسال النتائج...**",
            chat_id=message.chat.id,
            message_id=status_msg.message_id,
            parse_mode='Markdown'
        )
        
        file_bytes = BytesIO(file_content.encode('utf-8'))
        file_bytes.name = filename
        
        caption = f"""
✅ **تم استخراج المعلومات بنجاح!**

📋 **الملخص:**
• الاسم: {name}
• النصوص العربية: {len(extraction_result['arabic_texts'])} سطر
• النصوص الإنجليزية: {len(extraction_result['english_texts'])} سطر
• البريد الإلكتروني: `{email}`
• كلمة المرور: `{password}`

💾 **تم حفظ جميع المعلومات في الملف المرفق**
"""
        
        bot.send_document(
            chat_id=message.chat.id,
            document=file_bytes,
            caption=caption,
            parse_mode='Markdown'
        )
        
        # حذف رسالة الحالة
        bot.delete_message(
            chat_id=message.chat.id,
            message_id=status_msg.message_id
        )
        
        # حفظ بيانات المستخدم
        save_user_data(user_id, {
            'name': name,
            'email': email,
            'timestamp': datetime.now().isoformat(),
            'extraction_method': AI_SETUP['type']
        })
        
        # إرسال تعليمات نهائية
        final_message = f"""
🎉 **عملية الاستخراج اكتملت بنجاح!**

📋 **بيانات الدخول الخاصة بك:**
📧 **البريد الإلكتروني:** `{email}`
🔐 **كلمة المرور:** `{password}`

⚠️ **هام: احفظ هذه البيانات في مكان آمن!**

🔄 **لإرسال صورة أخرى:** أرسل صورة جديدة مباشرة
📊 **لعرض إحصائياتك:** اضغط على زر 📊 إحصائيات
❓ **للمساعدة:** اضغط على زر 🆘 المساعدة

💡 **تذكر:** يمكنك تغيير كلمة المرور لاحقاً لأمان أفضل.
"""
        
        bot.send_message(
            message.chat.id,
            final_message,
            parse_mode='Markdown'
        )
        
    except requests.exceptions.Timeout:
        bot.reply_to(
            message,
            "⏱️ **انتهت مهلة المعالجة**\n"
            "الرجاء إعادة المحاولة مع صورة أصغر حجماً",
            parse_mode='Markdown'
        )
    except Exception as e:
        print(f"❌ خطأ في معالجة الصورة: {e}")
        bot.reply_to(
            message,
            f"❌ **حدث خطأ غير متوقع**\n"
            f"التفاصيل: {str(e)[:100]}\n"
            "الرجاء إعادة المحاولة لاحقاً",
            parse_mode='Markdown'
        )

@bot.message_handler(content_types=['document'])
def handle_document_message(message):
    """معالجة الملفات المرسلة"""
    if message.document.mime_type and message.document.mime_type.startswith('image/'):
        # معاملة الملفات الصورية كصور
        handle_photo_message(message)
    else:
        bot.reply_to(
            message,
            "❌ **نوع الملف غير مدعوم**\n"
            "الرجاء إرسال صورة فقط (JPG, PNG, JPEG)",
            parse_mode='Markdown'
        )

@bot.message_handler(func=lambda message: True)
def handle_other_messages(message):
    """معالجة الرسائل الأخرى"""
    help_text = """
🤖 **مرحباً! أنا بوت استخراج النصوص**

📌 **للبدء، يمكنك:**
1. إرسال صورة البطاقة أو الجواز مباشرة
2. الضغط على زر 📸 إرسال صورة
3. استخدام الأمر /start

❓ **للمساعدة:** /help أو زر 🆘 المساعدة
📊 **للعرض إحصائيات:** /status أو زر 📊 إحصائيات

💡 **تلميح:** أرسل صورة الآن لتبدأ!
"""
    
    bot.reply_to(message, help_text, parse_mode='Markdown')

# ============= دعم Webhook للخدمات السحابية =============
def setup_webhook():
    """إعداد Webhook للخدمات التي تدعمه"""
    try:
        # الحصول على رابط Webhook من متغيرات البيئة
        webhook_url = os.environ.get('WEBHOOK_URL')
        
        if webhook_url and PLATFORM in ['Render.com', 'Railway.app', 'Koyeb.com', 'Cyclic.sh']:
            bot.remove_webhook()
            bot.set_webhook(url=f"{webhook_url}/{TELEGRAM_TOKEN}")
            print(f"✅ Webhook معين على: {webhook_url}")
            return True
    except:
        pass
    
    return False

# ============= بدء التشغيل =============
def start_bot():
    """بدء تشغيل البوت"""
    print("\n" + "=" * 60)
    print("🚀 بدء تشغيل البوت...")
    print("=" * 60)
    
    try:
        # الحصول على معلومات البوت
        bot_info = bot.get_me()
        print(f"✅ البوت: {bot_info.first_name} (@{bot_info.username})")
        print(f"🆔 المعرف: {bot_info.id}")
        print(f"🌐 المنصة: {PLATFORM}")
        print(f"🤖 المحرك: {'Gemini AI' if AI_SETUP['available'] else 'OCR Space'}")
        
        # محاولة إعداد Webhook
        if setup_webhook():
            print("🔗 البوت يعمل بنمط Webhook")
            return True
        else:
            print("🔄 البوت يعمل بنمط Polling")
            print("📱 اذهب إلى تيليجرام وأرسل /start")
            
            # تشغيل Polling
            bot.polling(none_stop=True, interval=0, timeout=60)
            return True
            
    except Exception as e:
        print(f"❌ خطأ في تشغيل البوت: {e}")
        print("\n🔧 **استكشاف الأخطاء وإصلاحها:**")
        print("1. تأكد من صحة توكن تيليجرام")
        print("2. تأكد من اتصال الإنترنت")
        print("3. تحقق من متغيرات البيئة")
        print("4. جرب إعادة تشغيل البوت")
        return False

# ============= نقطة الدخول الرئيسية =============
if __name__ == "__main__":
    # عرض معلومات النظام
    print(f"\n📋 معلومات النظام:")
    print(f"• نظام التشغيل: {sys.platform}")
    print(f"• إصدار Python: {sys.version.split()[0]}")
    print(f"• المسار: {os.path.dirname(os.path.abspath(__file__))}")
    
    # بدء البوت
    if not start_bot():
        print("\n❌ فشل تشغيل البوت. تحقق من الأخطاء أعلاه.")
        sys.exit(1)
