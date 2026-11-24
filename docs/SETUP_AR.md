# دليل التشغيل (من الهاتف فقط)

## ١) تحديث المشروع في Termux
بعد تنزيل `HAMO_AI_v1.0.0.zip` إلى مجلد التنزيلات:

```bash
termux-setup-storage            # مرة واحدة فقط، ووافق على الإذن
cd ~/HAMO_AI
unzip -o ~/storage/downloads/HAMO_AI_v1.0.0.zip
rm -f backend/requiremuvicorno  # ملف زائد غير مستخدم (اختياري)
bash tests/run_all.sh           # يجب أن ترى OK
bash start.sh
```
الملف `.env` ومجلد `.git` لا يتأثران بالفك لأنهما غير موجودين داخل الـ zip.

افتح Chrome على `http://127.0.0.1:8000` وجرّب: الصق فقرة، اختر «اشرح»، أرسل.

## ٢) رفع المشروع إلى GitHub (لبناء الـ APK سحابيًا)
في جلسة Termux ثانية (اترك الخادم يعمل في الأولى):

```bash
pkg install -y git gh
cd ~/HAMO_AI
git add -A
git commit -m "HAMO AI v1.0.0: educational modes, hardened backend, Android app"
gh auth login        # GitHub.com > HTTPS > Login with a web browser
gh repo create HAMO_AI --private --source=. --remote=origin --push
```
تأكد من `git status` أن `.env` غير مضاف (مُستثنى في `.gitignore`).

## ٣) تنزيل التطبيق
1. افتح المستودع على GitHub، تبويب **Actions**، وانتظر نحو ٥ دقائق حتى يصبح التشغيل أخضر.
2. افتح **Releases** ثم **HAMO AI (latest build)** ونزّل `HAMO-AI.apk` وثبّته (اسمح بالتثبيت من هذا المصدر، وإن ظهر تحذير Play Protect اختر «تثبيت على أي حال»).
3. إن فشل البناء (علامة حمراء) أرسل لي آخر ٣٠ سطرًا من سجل الخطوة الفاشلة.

## ٤) الاستخدام
1. شغّل الخادم في Termux: `bash start.sh`
2. افتح تطبيق HAMO AI، واضغط «١) منح إذن الظهور فوق التطبيقات» وفعّله، ثم ارجع.
3. اضغط «٢) تشغيل الزر العائم». يجب أن يظهر «الخادم: يعمل ✔» في الشاشة.
4. افتح Chrome وادخل أي درس، وانسخ فقرة، واضغط الزر **H**، ثم «لصق»، واختر نوع المساعدة، وأرسل.
5. زر ✕ في النافذة يغلقها ويعيدك للصفحة. لإزالة الزر العائم اضغط «إيقاف» في الإشعار أو داخل التطبيق.

## مشاكل شائعة
| المشكلة | الحل |
|---|---|
| «تعذر الاتصال بخادم HAMO AI» | شغّل `bash start.sh` في Termux |
| `Address already in use` | يوجد خادم قديم: اضغط CTRL+C في جلسته أو نفّذ `pkill -f backend/main.py` |
| الزر لا يظهر فوق Chrome | تأكد من الإذن، وفي هواتف شاومي/أوبو/هواوي فعّل «النوافذ المنبثقة/الظهور في الخلفية» من إعدادات التطبيق |
| زر «لصق» لا يلصق | اضغط مطولًا داخل المربع ثم «لصق» (Android يقيّد قراءة الحافظة أحيانًا) |
| توقف الخادم عند الخروج من Termux | `bash start.sh` يفعّل wake lock؛ وعطّل توفير البطارية لـ Termux |
| «App not installed» عند التحديث | ثبّت الإصدار الجديد بعد حذف القديم مرة واحدة فقط (يحدث إن اختلف مفتاح التوقيع) |
