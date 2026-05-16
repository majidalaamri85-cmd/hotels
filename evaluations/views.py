from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Prefetch, Count, Q
from django.views.decorators.cache import cache_control
from django.views.decorators.http import condition
from django.utils.decorators import method_decorator
from django.core.cache import cache
import logging
import json
from pathlib import Path
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
    return 'dashboard_data_v2'


def get_evaluation_stats(evaluation):
    responses = evaluation.responses.all()
    stats = responses.aggregate(
        total=Count('id'),
        ok=Count('id', filter=Q(result='OK')),
        no=Count('id', filter=Q(result='NO')),
        na=Count('id', filter=Q(result='NA')),
        failed_with_images=Count('id', filter=Q(result='NO', images__isnull=False), distinct=True),
        image_count=Count('images', distinct=True),
    )
    total = stats['total'] or 0
    reviewed = (stats['ok'] or 0) + (stats['no'] or 0) + (stats['na'] or 0)
    stats['reviewed'] = reviewed
    stats['remaining'] = max(total - reviewed, 0)
    stats['failed_without_images'] = max((stats['no'] or 0) - (stats['failed_with_images'] or 0), 0)
    stats['progress_percent'] = round((reviewed / total) * 100) if total else 0
    return stats


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


def ensure_criteria_seeded():
    """Populate criteria from bundled JSON if database has no criteria."""
    if Criterion.objects.exists():
        return False

    try:
        data_path = Path(__file__).resolve().parent / 'hotel_criteria_full.json'
        data = json.loads(data_path.read_text(encoding='utf-8'))

        for index, row in enumerate(data, start=1):
            section, _ = Section.objects.update_or_create(
                code=row['section_code'],
                defaults={
                    'title': row['section_title'],
                    'order': int(row['section_code']) if row['section_code'].isdigit() else index,
                },
            )
            subsection, _ = SubSection.objects.update_or_create(
                code=row['subsection_code'],
                defaults={
                    'section': section,
                    'title': row['subsection_title'],
                    'order': index,
                },
            )
            Criterion.objects.update_or_create(
                code=row['code'],
                defaults={
                    'subsection': subsection,
                    'title': row['title'],
                    'one_star': row['one_star'],
                    'two_star': row['two_star'],
                    'three_star': row['three_star'],
                    'four_star': row['four_star'],
                    'five_star': row['five_star'],
                    'corrective_action': row['corrective_action'],
                    'order': index,
                    'active': True,
                },
            )
        return True
    except Exception:
        logger.exception('Failed to auto-seed hotel criteria')
        return False


@cache_control(max_age=CACHE_TIMEOUT_SHORT, public=True)
def dashboard(request):
    """
    Dashboard view with optimized queries and caching.
    """
    if ensure_criteria_seeded():
        safe_cache_delete(get_dashboard_cache_key())
    cache_key = get_dashboard_cache_key()
    cached_data = safe_cache_get(cache_key)
    
    if cached_data:
        evaluations = cached_data['evaluations']
        criteria_count = cached_data['criteria_count']
        hotels_count = cached_data.get('hotels_count', 0)
        evaluations_count = cached_data.get('evaluations_count', len(evaluations))
    else:
        try:
            evaluations = list(
                Evaluation.objects.select_related('hotel').annotate(
                    failed_count=Count('responses', filter=Q(responses__result='NO')),
                    image_count=Count('responses__images', distinct=True),
                ).order_by('-id')[:20]
            )
            criteria_count = Criterion.objects.filter(active=True).count()
            hotels_count = Hotel.objects.count()
            evaluations_count = Evaluation.objects.count()
            cached_data = {
                'evaluations': evaluations,
                'criteria_count': criteria_count,
                'hotels_count': hotels_count,
                'evaluations_count': evaluations_count,
            }
            safe_cache_set(cache_key, cached_data, CACHE_TIMEOUT_SHORT)
        except Exception:
            logger.exception('Failed to load dashboard data')
            evaluations = []
            criteria_count = 0
            hotels_count = 0
            evaluations_count = 0
    
    return render(request, 'evaluations/dashboard.html', {
        'evaluations': evaluations,
        'criteria_count': criteria_count,
        'hotels_count': hotels_count,
        'evaluations_count': evaluations_count,
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


def hotel_edit(request, pk):
    """Edit an existing hotel."""
    hotel = get_object_or_404(Hotel, pk=pk)
    form = HotelForm(request.POST or None, instance=hotel)
    if form.is_valid():
        form.save()
        safe_cache_delete(get_dashboard_cache_key())
        messages.success(request, 'تم تحديث بيانات الفندق بنجاح')
        return redirect('dashboard')
    return render(request, 'evaluations/form.html', {
        'form': form,
        'title': f'تعديل بيانات {hotel.name}',
        'form_kind': 'hotel',
        'governorate_wilayat_map': GOVERNORATE_WILAYAT,
    })


def evaluation_edit(request, pk):
    """Edit basic evaluation info (hotel, date, status, team, notes)."""
    ev = get_object_or_404(Evaluation, pk=pk)
    form = EvaluationForm(request.POST or None, instance=ev)
    team_members = (
        request.POST.getlist('visiting_team_members[]')
        if request.method == 'POST'
        else ev.visiting_team.splitlines() or ['']
    )
    if form.is_valid():
        ev = form.save(commit=False)
        clean_members = parse_visiting_team_members(team_members)
        ev.visiting_team = '\n'.join(clean_members)
        ev.save()
        safe_cache_delete(get_dashboard_cache_key())
        messages.success(request, 'تم تحديث بيانات التقييم بنجاح')
        return redirect('evaluation_detail', pk=ev.pk)
    return render(request, 'evaluations/form.html', {
        'form': form,
        'title': f'تعديل تقييم {ev.hotel.name}',
        'form_kind': 'evaluation',
        'team_members': team_members if team_members else [''],
    })


def evaluation_create(request):
    """Create a new evaluation with optimized query."""
    ensure_criteria_seeded()
    if not Hotel.objects.exists():
        messages.warning(request, 'أضف فندقاً أولاً قبل بدء التقييم.')
        return redirect('hotel_create')

    form = EvaluationForm(request.POST or None)
    team_members = request.POST.getlist('visiting_team_members[]') if request.method == 'POST' else ['']
    active_criteria_qs = Criterion.objects.filter(active=True)
    criteria_qs = active_criteria_qs if active_criteria_qs.exists() else Criterion.objects.all()
    active_criteria_count = criteria_qs.count()
    sections = Section.objects.filter(
        subsections__criteria__in=criteria_qs
    ).annotate(
        criteria_count=Count(
            'subsections__criteria',
            filter=Q(subsections__criteria__in=criteria_qs),
            distinct=True,
        )
    ).distinct().order_by('order').prefetch_related(
        Prefetch(
            'subsections',
            queryset=SubSection.objects.filter(
                criteria__in=criteria_qs
            ).distinct().order_by('order').prefetch_related(
                Prefetch(
                    'criteria',
                    queryset=criteria_qs.order_by('order', 'id')
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
        active_criteria = criteria_qs.values(
            'id', 'corrective_action'
        )
        
        responses = []
        for c in active_criteria:
            result = request.POST.get(f'criterion_result_{c["id"]}', 'OK')
            responses.append(
                Response(
                    evaluation=ev,
                    criterion_id=c['id'],
                    result=result,
                    note=request.POST.get(f'criterion_note_{c["id"]}', '') if result == 'NO' else '',
                    corrective_action=request.POST.get(
                        f'criterion_action_{c["id"]}',
                        c['corrective_action']
                    ) if result == 'NO' else c['corrective_action'],
                )
            )
        Response.objects.bulk_create(responses, batch_size=100)

        response_images = []
        response_map = {
            response.criterion_id: response
            for response in ev.responses.all()
        }
        for criterion_id, response in response_map.items():
            if response.result != 'NO':
                continue
            for img in request.FILES.getlist(f'criterion_images_{criterion_id}'):
                response_images.append(ResponseImage(response=response, image=img))
        if response_images:
            ResponseImage.objects.bulk_create(response_images, batch_size=50)

        ev.recalculate()
        
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
    ensure_criteria_seeded()
    ev = get_object_or_404(Evaluation, pk=pk)

    # Keep old evaluations in sync with currently active criteria so items don't disappear.
    active_criteria_qs = Criterion.objects.filter(active=True)
    criteria_qs = active_criteria_qs if active_criteria_qs.exists() else Criterion.objects.all()
    active_criteria = list(
        criteria_qs.values('id', 'corrective_action')
    )
    existing_criterion_ids = set(
        ev.responses.values_list('criterion_id', flat=True)
    )
    missing_responses = [
        Response(
            evaluation=ev,
            criterion_id=criterion['id'],
            corrective_action=criterion['corrective_action'],
        )
        for criterion in active_criteria
        if criterion['id'] not in existing_criterion_ids
    ]
    if missing_responses:
        Response.objects.bulk_create(missing_responses, batch_size=100)
    
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
    ).prefetch_related('images')
    
    sections = Section.objects.order_by('order').prefetch_related(
        Prefetch(
            'subsections',
            queryset=SubSection.objects.filter(criteria__in=criteria_qs).distinct().order_by('order').prefetch_related(
                Prefetch(
                    'criteria',
                    queryset=criteria_qs.order_by('order', 'id')
                )
            )
        )
    ).filter(subsections__criteria__in=criteria_qs).distinct()
    
    # Create response map for template lookup
    responses = {r.criterion_id: r for r in responses_qs}
    
    return render(request, 'evaluations/evaluation_detail.html', {
        'ev': ev,
        'sections': sections,
        'responses': responses,
        'general_images': ev.general_images.all().order_by('-uploaded_at'),
        'stats': get_evaluation_stats(ev),
        'team_members': parse_visiting_team_members(ev.visiting_team.splitlines()),
        'has_active_criteria': bool(active_criteria),
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
        'stats': get_evaluation_stats(ev),
        'team_members': parse_visiting_team_members(ev.visiting_team.splitlines()),
    })
