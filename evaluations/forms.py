from django import forms
from .models import Hotel, Evaluation


GOVERNORATE_WILAYAT = {
    'مسقط': [
        ('مسقط', 'مسقط'),
        ('السيب', 'السيب'),
        ('بوشر', 'بوشر'),
        ('مطرح', 'مطرح'),
        ('العامرات', 'العامرات'),
        ('قريات', 'قريات'),
    ],
    'ظفار': [
        ('صلالة', 'صلالة'),
        ('طاقة', 'طاقة'),
        ('مرباط', 'مرباط'),
        ('سدح', 'سدح'),
        ('رخيوت', 'رخيوت'),
        ('ضلكوت', 'ضلكوت'),
        ('ثمريت', 'ثمريت'),
        ('شليم وجزر الحلانيات', 'شليم وجزر الحلانيات'),
    ],
    'مسندم': [
        ('خصب', 'خصب'),
        ('دبا', 'دبا'),
        ('بخاء', 'بخاء'),
        ('مدحاء', 'مدحاء'),
    ],
    'شمال الباطنة': [
        ('صحار', 'صحار'),
        ('شناص', 'شناص'),
        ('لوى', 'لوى'),
        ('صحم', 'صحم'),
        ('الخابورة', 'الخابورة'),
        ('السويق', 'السويق'),
    ],
    'جنوب الباطنة': [
        ('الرستاق', 'الرستاق'),
        ('العوابي', 'العوابي'),
        ('نخل', 'نخل'),
        ('وادي المعاول', 'وادي المعاول'),
        ('بركاء', 'بركاء'),
        ('المصنعة', 'المصنعة'),
    ],
    'الداخلية': [
        ('نزوى', 'نزوى'),
        ('بهلاء', 'بهلاء'),
        ('الحمراء', 'الحمراء'),
        ('منح', 'منح'),
        ('أدم', 'أدم'),
        ('إزكي', 'إزكي'),
        ('سمائل', 'سمائل'),
    ],
    'الشرقية شمال': [
        ('إبراء', 'إبراء'),
        ('المضيبي', 'المضيبي'),
        ('دماء والطائيين', 'دماء والطائيين'),
        ('بدية', 'بدية'),
        ('القابل', 'القابل'),
        ('وادي بني خالد', 'وادي بني خالد'),
    ],
    'الشرقية جنوب': [
        ('صور', 'صور'),
        ('الكامل والوافي', 'الكامل والوافي'),
        ('جعلان بني بوحسن', 'جعلان بني بوحسن'),
        ('جعلان بني بو علي', 'جعلان بني بو علي'),
        ('مصيرة', 'مصيرة'),
    ],
    'الظاهرة': [
        ('عبري', 'عبري'),
        ('ينقل', 'ينقل'),
        ('ضنك', 'ضنك'),
    ],
    'البريمي': [
        ('البريمي', 'البريمي'),
        ('محضة', 'محضة'),
        ('السنينة', 'السنينة'),
    ],
    'الوسطى': [
        ('هيما', 'هيما'),
        ('محوت', 'محوت'),
        ('الجازر', 'الجازر'),
        ('الدقم', 'الدقم'),
    ],
}

GOVERNORATE_CHOICES = [(name, name) for name in GOVERNORATE_WILAYAT]
WILAYAT_CHOICES = [choice for choices in GOVERNORATE_WILAYAT.values() for choice in choices]


def get_wilayat_choices(governorate=None):
    if governorate in GOVERNORATE_WILAYAT:
        return GOVERNORATE_WILAYAT[governorate]
    return WILAYAT_CHOICES


class HotelForm(forms.ModelForm):
    class Meta:
        model = Hotel
        fields = [
            'name',
            'governorate',
            'wilayat',
            'license_no',
            'rooms_count',
            'target_stars',
            'phone',
            'email',
            'latitude',
            'longitude',
        ]
        labels = {
            'name': 'اسم الفندق',
            'governorate': 'المحافظة',
            'wilayat': 'الولاية',
            'license_no': 'رقم الترخيص',
            'rooms_count': 'عدد الغرف',
            'target_stars': 'الفئة المستهدفة',
            'phone': 'رقم الهاتف',
            'email': 'البريد الإلكتروني',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['governorate'].widget = forms.Select(choices=[('', 'اختر المحافظة')] + GOVERNORATE_CHOICES)
        self.fields['wilayat'].widget = forms.Select(choices=[('', 'اختر الولاية')] + WILAYAT_CHOICES)
        self.fields['latitude'].widget = forms.HiddenInput()
        self.fields['longitude'].widget = forms.HiddenInput()
        self.fields['latitude'].widget.attrs.setdefault('step', '0.0000001')
        self.fields['longitude'].widget.attrs.setdefault('step', '0.0000001')
        for field in self.fields.values():
            css_class = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
            field.widget.attrs.setdefault('class', css_class)
            if not isinstance(field.widget, forms.Select):
                field.widget.attrs.setdefault('placeholder', field.label)

    def clean(self):
        cleaned = super().clean()
        governorate = cleaned.get('governorate')
        wilayat = cleaned.get('wilayat')
        if governorate and wilayat:
            allowed_wilayat = {value for value, _ in GOVERNORATE_WILAYAT.get(governorate, [])}
            if allowed_wilayat and wilayat not in allowed_wilayat:
                self.add_error('wilayat', 'الولاية المختارة لا تتبع هذه المحافظة.')
        return cleaned


class EvaluationForm(forms.ModelForm):
    class Meta:
        model = Evaluation
        fields = ['hotel', 'visit_date', 'status', 'general_notes']
        labels = {
            'hotel': 'الفندق',
            'visit_date': 'تاريخ الزيارة',
            'status': 'حالة التقييم',
            'general_notes': 'ملاحظات عامة',
        }
        widgets = {
            'visit_date': forms.DateInput(attrs={'type': 'date'}),
            'general_notes': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css_class = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
            field.widget.attrs.setdefault('class', css_class)
            if not isinstance(field.widget, forms.Select):
                field.widget.attrs.setdefault('placeholder', field.label)
