from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Prefetch, Count, Q
from django.views.decorators.cache import cache_control
from django.views.decorators.http import condition
from django.utils.decorators import method_decorator
from django.core.cache import cache
import logging
from .models import *
from .forms import HotelForm, EvaluationForm, GOVERNORATE_WILAYAT
import hashlib
from datetime import datetime


logger = logging.getLogger(__name__)

# Cache timeout constants (in seconds)
CACHE_TIMEOUT_SHORT = 300  # 5 minutes
CACHE_TIMEOUT_MEDIUM = 3600  # 1 hour
CACHE_TIMEOUT_LONG = 86400  # 24 hours


def parse_visiting_team_members(values):
    return [member.strip() for member in values if member and member.strip()]


def get_dashboard_cache_key():
    """Generate cache key for dashboard data"""
    return 'dashboard_data'


def safe_cache_get(key, default=None):
    """Read cache without breaking request flow if cache backend fails."""
    try:
        return cache.get(key, default)
    except Exception:
        return default


def safe_cache_set(key, value, timeout):
    """Write cache safely; ignore backend failures in production."""
    try:
        cache.set(key, value, timeout)
    except Exception:
        pass


def safe_cache_delete(key):
    """Delete cache key safely; ignore backend failures in production."""
    try:
        cache.delete(key)
    except Exception:
        pass


@cache_control(max_age=CACHE_TIMEOUT_SHORT, public=True)
def dashboard(request):
    """
    Dashboard view with optimized queries and caching.
    """
    cache_key = get_dashboard_cache_key()
    cached_data = safe_cache_get(cache_key)
    
    if cached_data:
        evaluations = cached_data['evaluations']
        criteria_count = cached_data['criteria_count']
    else:
        try:
            evaluations = list(
                Evaluation.objects.select_related('hotel').order_by('-id')[:20]
            )
            criteria_count = Criterion.objects.filter(active=True).count()
            cached_data = {
                'evaluations': evaluations,
                'criteria_count': criteria_count
            }
            safe_cache_set(cache_key, cached_data, CACHE_TIMEOUT_SHORT)
        except Exception:
            logger.exception('Failed to load dashboard data')
            evaluations = []
            criteria_count = 0
    
    return render(request, 'evaluations/dashboard.html', {
        'evaluations': evaluations,
        'criteria_count': criteria_count
    })


def hotel_create(request):
    """Create a new hotel with form validation."""
    form = HotelForm(request.POST or None)
    if form.is_valid():
        form.save()
        # Invalidate dashboard cache
        safe_cache_delete(get_dashboard_cache_key())
        messages.success(request, 'تم إضافة الفندق بنجاح')
        return redirect('dashboard')
    return render(request, 'evaluations/form.html', {
        'form': form,
        'title': 'إضافة فندق',
        'form_kind': 'hotel',
        'governorate_wilayat_map': GOVERNORATE_WILAYAT,
    })


def evaluation_create(request):
    """Create a new evaluation with optimized query."""
    form = EvaluationForm(request.POST or None)
    team_members = request.POST.getlist('visiting_team_members[]') if request.method == 'POST' else ['']
    active_criteria_count = Criterion.objects.filter(active=True).count()
    sections = Section.objects.filter(
        subsections__criteria__active=True
    ).annotate(
        criteria_count=Count(
            'subsections__criteria',
            filter=Q(subsections__criteria__active=True),
            distinct=True,
        )
    ).distinct().order_by('order').prefetch_related(
        Prefetch(
            'subsections',
            queryset=SubSection.objects.filter(
                criteria__active=True
            ).distinct().order_by('order').prefetch_related(
                Prefetch(
                    'criteria',
                    queryset=Criterion.objects.filter(active=True).order_by('order', 'id')
                )
            )
        )
    )

    if form.is_valid():
        ev = form.save(commit=False)
        ev.evaluator = request.user if request.user.is_authenticated else None
        clean_members = parse_visiting_team_members(team_members)
        ev.visiting_team = '\n'.join(clean_members)
        ev.additional_person = ''
        ev.save()
        
        # Batch create responses for all active criteria
        active_criteria = Criterion.objects.filter(active=True).values(
            'id', 'corrective_action'
        )
        
        responses = [
            Response(
                evaluation=ev,
                criterion_id=c['id'],
                corrective_action=c['corrective_action']
            )
            for c in active_criteria
        ]
        Response.objects.bulk_create(responses, batch_size=100)
        
        # Invalidate cache
        safe_cache_delete(get_dashboard_cache_key())
        messages.success(request, 'تم إنشاء التقييم بنجاح')
        return redirect('evaluation_detail', pk=ev.pk)
    
    return render(request, 'evaluations/form.html', {
        'form': form,
        'title': 'تقييم جديد',
        'form_kind': 'evaluation',
        'team_members': team_members if team_members else [''],
        'sections': sections,
        'active_criteria_count': active_criteria_count,
        'has_active_criteria': active_criteria_count > 0,
    })


@cache_control(max_age=CACHE_TIMEOUT_SHORT, public=True)
def evaluation_detail(request, pk):
    """
    Evaluation detail view with heavily optimized queries.
    Uses Prefetch for nested queries and select_related.
    """
    ev = get_object_or_404(Evaluation, pk=pk)
    
    if request.method == 'POST':
        # Batch update responses
        responses_map = {
            r.id: r for r in ev.responses.select_related('criterion')
        }
        
        updates = []
        images_to_create = []
        
        for response_id, response in responses_map.items():
            response.result = request.POST.get(f'result_{response_id}', response.result)
            response.note = request.POST.get(f'note_{response_id}', '')
            response.corrective_action = request.POST.get(
                f'action_{response_id}', 
                response.corrective_action
            )
            updates.append(response)
            
            # Collect images for batch creation
            for img in request.FILES.getlist(f'images_{response_id}'):
                images_to_create.append(
                    ResponseImage(response=response, image=img)
                )
        
        # Batch update and create
        if updates:
            Response.objects.bulk_update(updates, [
                'result', 'note', 'corrective_action'
            ], batch_size=100)
        
        if images_to_create:
            ResponseImage.objects.bulk_create(images_to_create, batch_size=50)

        # Save general evaluation images uploaded from the bottom section
        general_images = [
            EvaluationImage(evaluation=ev, image=img)
            for img in request.FILES.getlist('general_images')
        ]
        if general_images:
            EvaluationImage.objects.bulk_create(general_images, batch_size=50)
        
        # Recalculate score
        ev.recalculate()
        safe_cache_delete(get_dashboard_cache_key())
        messages.success(request, 'تم حفظ التقييم وحساب النتيجة')
        return redirect('evaluation_detail', pk=pk)
    
    # Optimize queries with Prefetch and select_related
    responses_qs = ev.responses.select_related('criterion').order_by(
        'criterion__order', 'criterion_id'
    )
    
    sections = Section.objects.order_by('order').prefetch_related(
        Prefetch(
            'subsections',
            queryset=SubSection.objects.order_by('order').prefetch_related(
                Prefetch(
                    'criteria',
                    queryset=Criterion.objects.filter(
                        active=True
                    ).order_by('order', 'id')
                )
            )
        )
    )
    
    # Create response map for template lookup
    responses = {r.criterion_id: r for r in responses_qs}
    
    return render(request, 'evaluations/evaluation_detail.html', {
        'ev': ev,
        'sections': sections,
        'responses': responses,
        'team_members': parse_visiting_team_members(ev.visiting_team.splitlines()),
    })


@cache_control(max_age=CACHE_TIMEOUT_MEDIUM, public=True)
def report_print(request, pk):
    """Print report view with optimized queries."""
    ev = get_object_or_404(
        Evaluation.objects.select_related('hotel'),
        pk=pk
    )
    all_rows = ev.responses.select_related('criterion').order_by(
        'criterion__order', 'criterion_id'
    ).prefetch_related('images')
    
    return render(request, 'evaluations/report_print.html', {
        'ev': ev,
        'all_rows': all_rows,
        'general_images': ev.general_images.all().order_by('-uploaded_at'),
        'team_members': parse_visiting_team_members(ev.visiting_team.splitlines()),
    })
