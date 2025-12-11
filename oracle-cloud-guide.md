# دليل Oracle Cloud

## الخطوات:
1. سجل في oracle.com/cloud/free
2. أنشئ VM مجانية
3. اتصل عبر SSH من هاتفك
4. شغل ملف الإعداد
5. البوت يعمل 24/7!

## تفاصيل الـ VM المجاني:
- 2 VPS مجاناً
- 24GB RAM لكل
- 200GB تخزين
- 10TB نقل بيانات/شهر

## الأوامر المهمة:
```bash
# تشغيل البوت يدوياً
python3 main.py

# كـ خدمة
sudo systemctl start telegram-bot
sudo systemctl status telegram-bot
sudo systemctl stop telegram-bot

# رؤية الـ logs
sudo journalctl -u telegram-bot -f
