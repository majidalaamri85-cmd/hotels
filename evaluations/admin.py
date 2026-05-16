from django.contrib import admin
from .models import Criterion, Evaluation, Hotel, Response, ResponseImage, Section, SubSection

admin.site.site_header = 'لوحة إدارة نظام تقييم الفنادق'
admin.site.site_title = 'إدارة تقييم الفنادق'
admin.site.index_title = 'إدارة البيانات والتقييمات'


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
	list_display = ('name', 'governorate', 'target_stars', 'rooms_count')
	search_fields = ('name', 'license_no', 'governorate', 'wilayat')
	list_filter = ('target_stars', 'governorate')


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
	list_display = ('code', 'title', 'order')
	search_fields = ('code', 'title')
	ordering = ('order',)


@admin.register(SubSection)
class SubSectionAdmin(admin.ModelAdmin):
	list_display = ('code', 'title', 'section', 'order')
	search_fields = ('code', 'title')
	list_filter = ('section',)
	ordering = ('section__order', 'order')


@admin.register(Criterion)
class CriterionAdmin(admin.ModelAdmin):
	list_display = ('code', 'subsection', 'active', 'order')
	search_fields = ('code', 'title')
	list_filter = ('active', 'subsection__section')
	ordering = ('subsection__section__order', 'subsection__order', 'order')


@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
	list_display = ('hotel', 'visit_date', 'status', 'score', 'recommendation')
	search_fields = ('hotel__name', 'recommendation')
	list_filter = ('status', 'visit_date')
	date_hierarchy = 'visit_date'


@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
	list_display = ('evaluation', 'criterion', 'result')
	search_fields = ('criterion__code', 'criterion__title', 'evaluation__hotel__name')
	list_filter = ('result',)


@admin.register(ResponseImage)
class ResponseImageAdmin(admin.ModelAdmin):
	list_display = ('response', 'caption', 'uploaded_at')
	search_fields = ('caption', 'response__criterion__code')
	date_hierarchy = 'uploaded_at'
