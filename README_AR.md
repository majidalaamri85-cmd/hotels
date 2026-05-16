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
python manage.py migrate
python manage.py seed_hotel_criteria
python manage.py createsuperuser
python manage.py runserver
```

## النشر على Render
1. ارفع المشروع إلى GitHub.
2. في Render اختر New Blueprint أو Web Service.
3. اربط المستودع.
4. سيستخدم Render ملف `render.yaml` لإنشاء Web Service و PostgreSQL.
5. تأكد من Environment Variables: `SECRET_KEY`, `DEBUG=False`, `DATABASE_URL`.

## ملاحظة مهمة
تم إدخال كل البنود كأكواد رسمية ونصوص عناوين مستخرجة قدر الإمكان من ملف PDF. إذا رغبت بنسخة قانونية 100% حرفياً لكل متطلبات النجوم داخل كل خلية من الجداول، يلزم تحويل الجداول من PDF إلى Excel/CSV ومراجعتها يدوياً بسبب طبيعة تنسيق PDF العربي الممسوح/المختلط.
