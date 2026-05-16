# النسخة النهائية الكاملة – نظام تقييم وتصنيف الفنادق

هذه نسخة Django جاهزة مبدئياً لوزارة التراث والسياحة، مبنية على ملف **معايير التصنيف للفنادق باللغة العربية 2013/2014**.

## ما تم تضمينه
- إدخال جميع أكواد البنود الرسمية حسب جدول المحتويات ونطاقات البنود: **360 بنداً**.
- نفس الترقيم الرسمي للأقسام والبنود.
- واجهة عربية RTL حكومية.
- رفع ملاحظات وإجراءات تصحيحية وصور متعددة لكل بند.
- حساب النتيجة تلقائياً.
- تقرير Word رسمي للبنود غير المستوفية.
- جاهزية Render/PostgreSQL عبر `render.yaml`.

## التشغيل المحلي
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py seed_hotel_criteria
python manage.py createsuperuser
python manage.py runserver
```

## الرفع إلى GitHub (أول مرة)
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/<username>/<repo>.git
git push -u origin main
```

> ملاحظة: ملف `.gitignore` مهيأ بالفعل لتجاهل `db.sqlite3` و`media` و`staticfiles` وملفات البيئة.

## النشر على Render
1. ارفع المشروع إلى GitHub.
2. في Render اختر New Blueprint أو Web Service.
3. اربط المستودع.
4. سيستخدم Render ملف `render.yaml` لإنشاء Web Service و PostgreSQL تلقائياً.
5. تأكد من Environment Variables التالية (أو اترك الافتراضي الموجود في `render.yaml`):
	- `SECRET_KEY` (يتولد تلقائياً)
	- `DEBUG=False`
	- `ALLOWED_HOSTS=.onrender.com` أو اسم الدومين النهائي
	- `DATABASE_URL` (يتم ربطه تلقائياً بقاعدة Render PostgreSQL)
	- `CACHE_BACKEND=db` (الافتراضي، ويمكن `locmem` عند الحاجة)
6. بعد أول نشر، افتح رابط الخدمة وأنشئ مستخدم الإدارة:
	- من Render Shell: `python manage.py createsuperuser`
7. لإضافة دومين مخصص لاحقاً:
	- أضف الدومين في Render
	- حدّث `ALLOWED_HOSTS` و`CSRF_TRUSTED_ORIGINS` بالقيم الجديدة.

## ملاحظة مهمة
تم إدخال كل البنود كأكواد رسمية ونصوص عناوين مستخرجة قدر الإمكان من ملف PDF. إذا رغبت بنسخة قانونية 100% حرفياً لكل متطلبات النجوم داخل كل خلية من الجداول، يلزم تحويل الجداول من PDF إلى Excel/CSV ومراجعتها يدوياً بسبب طبيعة تنسيق PDF العربي الممسوح/المختلط.
