from django import forms
from .models import Hotel, Evaluation


class HotelForm(forms.ModelForm):
    class Meta:
        model = Hotel
        fields = '__all__'
        labels = {
            'name': 'اسم الفندق',
            'governorate': 'المحافظة',
            'wilayat': 'الولاية',
            'license_no': 'رقم الترخيص',
            'rooms_count': 'عدد الغرف',
            'target_stars': 'الفئة المستهدفة',
            'phone': 'رقم الهاتف',
            'email': 'البريد الإلكتروني',
            'latitude': 'خط العرض',
            'longitude': 'خط الطول',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css_class = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
            field.widget.attrs.setdefault('class', css_class)
            field.widget.attrs.setdefault('placeholder', field.label)


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
            field.widget.attrs.setdefault('placeholder', field.label)
