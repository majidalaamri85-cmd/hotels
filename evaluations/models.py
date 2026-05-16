from django.db import models
from django.db.models import Count, Q
from django.contrib.auth.models import User


class Hotel(models.Model):
    STAR_CHOICES = [(1, 'نجمة واحدة'), (2, 'نجمتان'), (3, 'ثلاث نجوم'), (4, 'أربع نجوم'), (5, 'خمس نجوم')]
    name = models.CharField(max_length=255, verbose_name='اسم الفندق')
    governorate = models.CharField(max_length=120, blank=True, verbose_name='المحافظة')
    wilayat = models.CharField(max_length=120, blank=True, verbose_name='الولاية')
    license_no = models.CharField(max_length=100, blank=True, verbose_name='رقم الترخيص')
    rooms_count = models.PositiveIntegerField(default=0, verbose_name='عدد الغرف')
    target_stars = models.PositiveSmallIntegerField(choices=STAR_CHOICES, default=3, verbose_name='الفئة المستهدفة')
    phone = models.CharField(max_length=50, blank=True, verbose_name='رقم الهاتف')
    email = models.EmailField(blank=True, verbose_name='البريد الإلكتروني')
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True, verbose_name='خط العرض')
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True, verbose_name='خط الطول')

    class Meta:
        verbose_name = 'فندق'
        verbose_name_plural = 'الفنادق'

    def __str__(self):
        return self.name


class Section(models.Model):
    code = models.CharField(max_length=20, unique=True, verbose_name='الكود')
    title = models.CharField(max_length=255, verbose_name='العنوان')
    order = models.PositiveIntegerField(default=0, verbose_name='الترتيب')

    class Meta:
        verbose_name = 'قسم رئيسي'
        verbose_name_plural = 'الأقسام الرئيسية'

    def __str__(self):
        return f'{self.code} - {self.title}'


class SubSection(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='subsections', verbose_name='القسم الرئيسي')
    code = models.CharField(max_length=20, unique=True, verbose_name='الكود')
    title = models.CharField(max_length=255, verbose_name='العنوان')
    order = models.PositiveIntegerField(default=0, verbose_name='الترتيب')

    class Meta:
        verbose_name = 'قسم فرعي'
        verbose_name_plural = 'الأقسام الفرعية'

    def __str__(self):
        return f'{self.code} - {self.title}'


class Criterion(models.Model):
    subsection = models.ForeignKey(SubSection, on_delete=models.CASCADE, related_name='criteria', verbose_name='القسم الفرعي')
    code = models.CharField(max_length=30, unique=True, verbose_name='الكود')
    title = models.TextField(verbose_name='البند')
    one_star = models.TextField(blank=True, verbose_name='متطلبات نجمة واحدة')
    two_star = models.TextField(blank=True, verbose_name='متطلبات نجمتين')
    three_star = models.TextField(blank=True, verbose_name='متطلبات ثلاث نجوم')
    four_star = models.TextField(blank=True, verbose_name='متطلبات أربع نجوم')
    five_star = models.TextField(blank=True, verbose_name='متطلبات خمس نجوم')
    corrective_action = models.TextField(blank=True, verbose_name='الإجراء التصحيحي الافتراضي')
    active = models.BooleanField(default=True, verbose_name='نشط')
    order = models.PositiveIntegerField(default=0, verbose_name='الترتيب')

    class Meta:
        verbose_name = 'معيار'
        verbose_name_plural = 'المعايير'

    def requirement_for(self, stars):
        return {1: self.one_star, 2: self.two_star, 3: self.three_star, 4: self.four_star, 5: self.five_star}.get(stars, '')

    def __str__(self):
        return self.code


class Evaluation(models.Model):
    STATUS = [('DRAFT', 'مسودة'), ('FINAL', 'معتمد')]
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='evaluations', verbose_name='الفندق')
    evaluator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='المقيّم')
    visit_date = models.DateField(verbose_name='تاريخ الزيارة')
    status = models.CharField(max_length=20, choices=STATUS, default='DRAFT', verbose_name='حالة التقييم')
    general_notes = models.TextField(blank=True, verbose_name='ملاحظات عامة')
    score = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='النتيجة')
    recommendation = models.CharField(max_length=200, blank=True, verbose_name='التوصية')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ آخر تحديث')

    class Meta:
        verbose_name = 'تقييم'
        verbose_name_plural = 'التقييمات'

    def recalculate(self):
        stats = self.responses.exclude(result='NA').aggregate(
            total=Count('id'),
            ok=Count('id', filter=Q(result='OK')),
        )
        total = stats['total'] or 0
        ok = stats['ok'] or 0
        self.score = round((ok / total) * 100, 2) if total else 0
        self.recommendation = (
            'مستوفي' if self.score >= 90 else
            'اعتماد مشروط/إعادة زيارة' if self.score >= 70 else
            'غير مستوفي حالياً'
        )
        self.save(update_fields=['score', 'recommendation'])


class Response(models.Model):
    RESULT = [('OK', 'مستوفي'), ('NO', 'غير مستوفي'), ('NA', 'لا ينطبق')]
    evaluation = models.ForeignKey(Evaluation, on_delete=models.CASCADE, related_name='responses', verbose_name='التقييم')
    criterion = models.ForeignKey(Criterion, on_delete=models.CASCADE, verbose_name='المعيار')
    result = models.CharField(max_length=2, choices=RESULT, default='OK', verbose_name='الحالة')
    note = models.TextField(blank=True, verbose_name='الملاحظة')
    corrective_action = models.TextField(blank=True, verbose_name='الإجراء التصحيحي')

    class Meta:
        unique_together = ('evaluation', 'criterion')
        verbose_name = 'استجابة بند'
        verbose_name_plural = 'استجابات البنود'


class ResponseImage(models.Model):
    response = models.ForeignKey(Response, on_delete=models.CASCADE, related_name='images', verbose_name='الاستجابة')
    image = models.ImageField(upload_to='evaluation_images/%Y/%m/', verbose_name='الصورة')
    caption = models.CharField(max_length=255, blank=True, verbose_name='وصف الصورة')
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الرفع')

    class Meta:
        verbose_name = 'صورة مرفقة'
        verbose_name_plural = 'الصور المرفقة'


class EvaluationImage(models.Model):
    evaluation = models.ForeignKey(
        Evaluation,
        on_delete=models.CASCADE,
        related_name='general_images',
        verbose_name='التقييم'
    )
    image = models.ImageField(upload_to='evaluation_images/general/%Y/%m/', verbose_name='الصورة')
    caption = models.CharField(max_length=255, blank=True, verbose_name='وصف الصورة')
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الرفع')

    class Meta:
        verbose_name = 'صورة عامة للتقييم'
        verbose_name_plural = 'الصور العامة للتقييم'
