from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST, require_GET, require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie
from django.middleware.csrf import get_token
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, Sum, F, ExpressionWrapper, FloatField
from django.core.paginator import Paginator
from .models import TableroProduccion, UnidadNegocio, MovimientoCombustible, Equipo, TipoCombustible, UnidadProduccion, TipoOperacion, Empleado
from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.mail import EmailMessage
from django.conf import settings
import json
import threading
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from django.contrib.auth import update_session_auth_hash
from datetime import datetime, date, timedelta
from collections import defaultdict
import calendar


@ensure_csrf_cookie
@require_GET
def api_csrf(request):
    return JsonResponse({'detail': 'CSRF cookie set', 'csrfToken': get_token(request)})


@require_POST
def api_login(request):
    try:
        data = json.loads(request.body.decode())
    except Exception:
        return JsonResponse({'detail': 'Invalid request'}, status=400)

    username = data.get('username')
    password = data.get('password')
    user = authenticate(request, username=username, password=password)
    if user is not None:
        auth_login(request, user)
        return JsonResponse({'username': user.username, 'email': user.email})
    return JsonResponse({'detail': 'Invalid credentials'}, status=400)


@require_POST
def api_logout(request):
    auth_logout(request)
    return JsonResponse({'detail': 'Logged out'})


@login_required
def api_user(request):
    user = request.user
    # GET: devolver datos del usuario
    if request.method == 'GET':
        return JsonResponse({'username': user.username, 'email': user.email})

    # PUT: actualizar username/email (body JSON)
    if request.method in ('PUT', 'PATCH'):
        try:
            data = json.loads(request.body.decode())
        except Exception:
            return JsonResponse({'detail': 'Invalid request'}, status=400)

        username = data.get('username')
        email = data.get('email')
        changed = False
        if username and username != user.username:
            user.username = username
            changed = True
        if email and email != user.email:
            user.email = email
            changed = True

        if changed:
            try:
                user.save()
            except Exception as e:
                return JsonResponse({'detail': 'Could not save user', 'error': str(e)}, status=500)

        return JsonResponse({'username': user.username, 'email': user.email})

    return JsonResponse({'detail': 'Method not allowed'}, status=405)


@login_required
def api_user_password(request):
    """POST: change current user's password
    body: { current_password, new_password, new_password_confirm }
    """
    if request.method != 'POST':
        return JsonResponse({'detail': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body.decode())
    except Exception:
        return JsonResponse({'detail': 'Invalid request'}, status=400)

    current = data.get('current_password')
    newp = data.get('new_password')
    newp2 = data.get('new_password_confirm')

    if not current or not newp or not newp2:
        return JsonResponse({'detail': 'Missing fields'}, status=400)

    if newp != newp2:
        return JsonResponse({'detail': 'New passwords do not match'}, status=400)

    user = request.user
    if not user.check_password(current):
        return JsonResponse({'detail': 'Current password incorrect'}, status=400)

    # Basic password validation: require at least 6 chars (adjust as needed)
    if len(newp) < 6:
        return JsonResponse({'detail': 'New password too short (min 6 chars)'}, status=400)

    try:
        user.set_password(newp)
        user.save()
        # keep the user authenticated in this session
        try:
            update_session_auth_hash(request, user)
        except Exception:
            pass
    except Exception as e:
        return JsonResponse({'detail': 'Could not update password', 'error': str(e)}, status=500)

    return JsonResponse({'detail': 'Password updated'})


@login_required
def api_produccion_data(request):
    """
    Devuelve datos agregados de producción filtrados por fecha y unidad_negocio.
    Query params: fecha_desde, fecha_hasta, unidad_negocio_id, tipo_operacion_id, equipo_id
    """
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    unidad_negocio_id = request.GET.get('unidad_negocio_id')
    tipo_operacion_id = request.GET.get('tipo_operacion_id')
    unidad_produccion_id = request.GET.get('unidad_produccion_id')
    equipo_id = request.GET.get('equipo_id')
    empleado_id = request.GET.get('empleado_id')

    qs = TableroProduccion.objects.all()

    if fecha_desde:
        qs = qs.filter(fecha__gte=fecha_desde)
    if fecha_hasta:
        qs = qs.filter(fecha__lte=fecha_hasta)
    if unidad_negocio_id:
        qs = qs.filter(unidad_negocio_id=unidad_negocio_id)
    if tipo_operacion_id:
        qs = qs.filter(tipo_operacion_id=tipo_operacion_id)
    if unidad_produccion_id:
        qs = qs.filter(unidad_produccion_id=unidad_produccion_id)
    if equipo_id:
        qs = qs.filter(equipo_id=equipo_id)
    if empleado_id:
        qs = qs.filter(empleado_id=empleado_id)

    # Calcular horas trabajadas (hr_fin - hr_inicio) y agrupar por fecha
    qs = qs.annotate(
        horas_trabajadas=ExpressionWrapper(
            F('hr_fin') - F('hr_inicio'),
            output_field=FloatField()
        )
    ).values('fecha').annotate(
        total_horas=Sum('horas_trabajadas'),
        total_produccion=Sum('produccion'),
        horas_no_operativas=Sum('hrs_no_operativas')
    ).order_by('fecha')

    data = list(qs)
    # Convertir fecha a string para JSON y redondear horas a 2 decimales
    for item in data:
        item['fecha'] = item['fecha'].isoformat() if item['fecha'] else None
        if item['total_horas'] is not None:
            item['total_horas'] = round(float(item['total_horas']), 2)
        if item.get('horas_no_operativas') is not None:
            # hrs_no_operativas stored as integer; return as number with 2 decimals
            item['horas_no_operativas'] = round(float(item['horas_no_operativas'] or 0), 2)

    return JsonResponse({'data': data})



@login_required
def api_produccion_kpis(request):
    """
    Devuelve KPIs agregados para las producciones filtradas.
    Query params: fecha_desde, fecha_hasta, unidad_negocio_id, tipo_operacion_id, equipo_id
    KPIs devueltos: total_horas, total_produccion, avg_production_per_hour,
    dias_activos, entradas
    """
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    unidad_negocio_id = request.GET.get('unidad_negocio_id')
    tipo_operacion_id = request.GET.get('tipo_operacion_id')
    equipo_id = request.GET.get('equipo_id')
    empleado_id = request.GET.get('empleado_id')

    qs = TableroProduccion.objects.all()
    if fecha_desde:
        qs = qs.filter(fecha__gte=fecha_desde)
    if fecha_hasta:
        qs = qs.filter(fecha__lte=fecha_hasta)
    if unidad_negocio_id:
        qs = qs.filter(unidad_negocio_id=unidad_negocio_id)
    if tipo_operacion_id:
        qs = qs.filter(tipo_operacion_id=tipo_operacion_id)
    if equipo_id:
        qs = qs.filter(equipo_id=equipo_id)
    if empleado_id:
        qs = qs.filter(empleado_id=empleado_id)

    # calcular horas trabajadas por registro
    qs = qs.annotate(
        horas_trabajadas=ExpressionWrapper(
            F('hr_fin') - F('hr_inicio'),
            output_field=FloatField()
        )
    )

    agg = qs.aggregate(
        total_horas=Sum('horas_trabajadas'),
        total_produccion=Sum('produccion'),
        entradas=Sum(ExpressionWrapper(F('id') * 0 + 1, output_field=FloatField())),
        horas_no_operativas=Sum('hrs_no_operativas')
    )

    # contar dias activos
    dias_activos = qs.values('fecha').distinct().count()

    total_horas = float(agg.get('total_horas') or 0)
    total_produccion = float(agg.get('total_produccion') or 0)
    entradas = int(agg.get('entradas') or 0)
    horas_no_operativas = float(agg.get('horas_no_operativas') or 0)
    avg_production_per_hour = (total_produccion / total_horas) if total_horas > 0 else 0

    # redondear a 2 decimales
    result = {
        'total_horas': round(total_horas, 2),
        'total_produccion': round(total_produccion, 2),
        'avg_production_per_hour': round(avg_production_per_hour, 2),
        'dias_activos': dias_activos,
        'entradas': entradas,
        'horas_no_operativas': round(horas_no_operativas, 2),
    }

    return JsonResponse({'kpis': result})


def _dashboard_round(value, digits=2):
    try:
        return round(float(value or 0), digits)
    except (TypeError, ValueError):
        return 0


def _dashboard_label(value, fallback='-'):
    text = str(value or '').strip()
    return text if text else fallback


def _dashboard_is_hours_unit(value):
    return _dashboard_label(value).lower() == 'horas'


def _dashboard_skips_hour_metrics(segment):
    tipo_movil = _dashboard_label(segment.get('tipo_movil'), '').lower()
    tipo_operacion = _dashboard_label(segment.get('tipo_operacion'), '').lower()
    return tipo_movil == 'camion' or tipo_operacion in ('transporte', 'transporte carreton')


def _dashboard_severity(value, baseline, yellow_pct, red_pct, direction='higher'):
    value = float(value or 0)
    baseline = float(baseline or 0)
    if baseline <= 0:
        return 'sin_historico', 0

    if direction == 'lower':
        diff_pct = ((baseline - value) / baseline) * 100
    else:
        diff_pct = ((value - baseline) / baseline) * 100

    if diff_pct >= red_pct:
        return 'rojo', round(diff_pct, 1)
    if diff_pct >= yellow_pct:
        return 'amarillo', round(diff_pct, 1)
    return 'verde', round(diff_pct, 1)


def _dashboard_dates(request):
    today = date.today()
    fecha_desde_raw = request.GET.get('fecha_desde')
    fecha_hasta_raw = request.GET.get('fecha_hasta')

    try:
        fecha_hasta = datetime.strptime(fecha_hasta_raw, '%Y-%m-%d').date() if fecha_hasta_raw else today
        fecha_desde = datetime.strptime(fecha_desde_raw, '%Y-%m-%d').date() if fecha_desde_raw else fecha_hasta.replace(day=1)
    except ValueError:
        return None, None, JsonResponse({'detail': 'Formato de fecha inválido. Usar YYYY-MM-DD.'}, status=400)

    if fecha_desde > fecha_hasta:
        return None, None, JsonResponse({'detail': 'fecha_desde no puede ser posterior a fecha_hasta.'}, status=400)

    return fecha_desde, fecha_hasta, None


def _dashboard_apply_filters(qs, filters):
    if filters.get('unidad_negocio_id'):
        qs = qs.filter(unidad_negocio_id=filters['unidad_negocio_id'])
    if filters.get('tipo_operacion_id'):
        qs = qs.filter(tipo_operacion_id=filters['tipo_operacion_id'])
    if filters.get('unidad_produccion_id'):
        qs = qs.filter(unidad_produccion_id=filters['unidad_produccion_id'])
    if filters.get('equipo_id'):
        qs = qs.filter(equipo_id=filters['equipo_id'])
    if filters.get('empleado_id'):
        qs = qs.filter(empleado_id=filters['empleado_id'])
    return qs


def _dashboard_segment_key(row):
    return (
        row.get('unidad_negocio_id'),
        row.get('tipo_operacion_id'),
        row.get('unidad_produccion_id'),
        row.get('equipo_id'),
    )


def _dashboard_segment_label(row):
    unidad = _dashboard_label(row.get('unidad_negocio__descripcion'), f"Unidad {row.get('unidad_negocio_id')}")
    tipo = _dashboard_label(row.get('tipo_operacion__descripcion'), f"Tipo {row.get('tipo_operacion_id')}")
    unidad_prod = _dashboard_label(row.get('unidad_produccion__descripcion'), f"Unidad prod. {row.get('unidad_produccion_id')}")
    equipo = _dashboard_label(row.get('equipo__descripcion') or row.get('equipo_label'), f"Equipo {row.get('equipo_id')}")
    return unidad, tipo, unidad_prod, equipo


def _dashboard_shift_month(value, months_back):
    month_index = (value.month - 1) - months_back
    year = value.year + (month_index // 12)
    month = (month_index % 12) + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _dashboard_mtd_window(anchor_date, months_back=0):
    end_date = _dashboard_shift_month(anchor_date, months_back)
    return end_date.replace(day=1), end_date


def _dashboard_fuel_by_produccion(qs_prod):
    prod_ids = list(qs_prod.values_list('id', flat=True))
    if not prod_ids:
        return {}

    return {
        row['idtabla']: float(row['total_litros'] or 0)
        for row in (
            MovimientoCombustible.objects
            .filter(idtabla__in=prod_ids)
            .filter(tipo_combustible__descripcion__iregex=r'(gasoil|gas.?oil|nafta|diesel)')
            .exclude(tipo_combustible__descripcion__icontains='aceite')
            .values('idtabla')
            .annotate(total_litros=Sum('egreso'))
        )
    }


def _dashboard_build_segments(qs_prod, fuel_by_prod, include_daily=False):
    horas_expr = ExpressionWrapper(F('hr_fin') - F('hr_inicio'), output_field=FloatField())
    qs = qs_prod.annotate(horas_trabajadas=horas_expr)

    rows = qs.values(
        'id',
        'fecha',
        'unidad_negocio_id',
        'unidad_negocio__descripcion',
        'tipo_operacion_id',
        'tipo_operacion__descripcion',
        'unidad_produccion_id',
        'unidad_produccion__descripcion',
        'equipo_id',
    ).annotate(
        produccion_total=Sum('produccion'),
        horas_total=Sum('horas_trabajadas'),
        horas_no_operativas=Sum('hrs_no_operativas'),
    )

    equipo_ids = {row['equipo_id'] for row in rows if row.get('equipo_id')}
    equipos_map = {
        equipo['id']: {
            'descripcion': _dashboard_label(equipo['descripcion'], f"Equipo {equipo['id']}"),
            'tipo_movil': _dashboard_label(equipo['tipo_movil__descripcion'], ''),
        }
        for equipo in Equipo.objects.filter(id__in=list(equipo_ids)).values(
            'id',
            'descripcion',
            'tipo_movil__descripcion',
        )
    }

    segments = {}
    daily = defaultdict(lambda: {'produccion': 0.0, 'horas': 0.0, 'combustible': 0.0})

    for row in rows:
        equipo_meta = equipos_map.get(row.get('equipo_id'), {})
        row['equipo_label'] = equipo_meta.get('descripcion')
        key = _dashboard_segment_key(row)
        unidad, tipo, unidad_prod, equipo = _dashboard_segment_label(row)
        segment = segments.setdefault(key, {
            'unidad_negocio_id': row.get('unidad_negocio_id'),
            'unidad_negocio': unidad,
            'tipo_operacion_id': row.get('tipo_operacion_id'),
            'tipo_operacion': tipo,
            'unidad_produccion_id': row.get('unidad_produccion_id'),
            'unidad_produccion': unidad_prod,
            'equipo_id': row.get('equipo_id'),
            'equipo': equipo,
            'tipo_movil': equipo_meta.get('tipo_movil', ''),
            'produccion': 0.0,
            'horas': 0.0,
            'horas_no_operativas': 0.0,
            'combustible': 0.0,
            'registros': 0,
            'dias': set(),
        })

        litros = float(fuel_by_prod.get(row['id'], 0))
        produccion = float(row.get('produccion_total') or 0)
        horas = float(row.get('horas_total') or 0)
        no_operativas = float(row.get('horas_no_operativas') or 0)

        segment['produccion'] += produccion
        segment['horas'] += horas
        segment['horas_no_operativas'] += no_operativas
        segment['combustible'] += litros
        segment['registros'] += 1
        if row.get('fecha'):
            segment['dias'].add(row['fecha'])

        if include_daily and row.get('fecha'):
            day = row['fecha'].isoformat()
            daily[day]['produccion'] += produccion
            daily[day]['horas'] += horas
            daily[day]['combustible'] += litros

    return segments, daily


def _dashboard_finalize_segments(segments, baseline_segments=None):
    baseline_segments = baseline_segments or {}
    finalized = []
    alertas = []

    for key, segment in segments.items():
        unidad_prod = segment['unidad_produccion']
        is_hours = _dashboard_is_hours_unit(unidad_prod)
        skips_hour_metrics = _dashboard_skips_hour_metrics(segment)
        horas = segment['horas']
        produccion = segment['produccion']
        combustible = segment['combustible']
        dias = max(len(segment['dias']), 1)

        prod_por_hora = None if is_hours or skips_hour_metrics or horas <= 0 else produccion / horas
        litros_por_hora = combustible / horas if horas > 0 and not skips_hour_metrics else None
        litros_por_unidad = combustible / produccion if produccion > 0 and not is_hours else None
        actividad_por_dia = horas / dias if is_hours else None

        baseline = baseline_segments.get(key, {})
        baseline_horas = baseline.get('horas', 0)
        baseline_prod = baseline.get('produccion', 0)
        baseline_comb = baseline.get('combustible', 0)
        baseline_dias = max(len(baseline.get('dias', set())), 1)

        baseline_prod_metric = None
        current_prod_metric = None
        metric_label = 'Prod/hora'
        if skips_hour_metrics:
            current_prod_metric = (produccion / dias) if produccion > 0 else None
            baseline_prod_metric = (baseline_prod / baseline_dias) if baseline_prod > 0 else 0
            metric_label = f"{unidad_prod}/día"
        elif is_hours:
            current_prod_metric = actividad_por_dia or 0
            baseline_prod_metric = (baseline_horas / baseline_dias) if baseline_horas > 0 else 0
            metric_label = 'Horas/día'
        elif horas > 0:
            current_prod_metric = prod_por_hora or 0
            baseline_prod_metric = (baseline_prod / baseline_horas) if baseline_horas > 0 else 0

        prod_severity = 'sin_historico'
        prod_diff = 0
        if current_prod_metric is not None and not skips_hour_metrics:
            prod_severity, prod_diff = _dashboard_severity(current_prod_metric, baseline_prod_metric, 8, 15, direction='lower')

        fuel_baseline = (baseline_comb / baseline_horas) if baseline_horas > 0 and not skips_hour_metrics else 0
        fuel_severity, fuel_diff = ('sin_historico', 0) if skips_hour_metrics else _dashboard_severity(litros_por_hora or 0, fuel_baseline, 10, 20, direction='higher')

        status = 'verde'
        if 'rojo' in (prod_severity, fuel_severity) or horas < 0 or produccion < 0:
            status = 'rojo'
        elif 'amarillo' in (prod_severity, fuel_severity):
            status = 'amarillo'
        elif 'sin_historico' in (prod_severity, fuel_severity):
            status = 'sin_historico'

        result = {
            **{k: v for k, v in segment.items() if k != 'dias'},
            'dias_activos': len(segment['dias']),
            'produccion': _dashboard_round(produccion),
            'horas': _dashboard_round(horas),
            'horas_no_operativas': _dashboard_round(segment['horas_no_operativas']),
            'combustible': _dashboard_round(combustible),
            'prod_por_hora': _dashboard_round(prod_por_hora) if prod_por_hora is not None else None,
            'litros_por_hora': _dashboard_round(litros_por_hora) if litros_por_hora is not None else None,
            'litros_por_unidad': _dashboard_round(litros_por_unidad) if litros_por_unidad is not None else None,
            'actividad_por_dia': _dashboard_round(actividad_por_dia) if actividad_por_dia is not None else None,
            'metric_label': metric_label,
            'metric_value': _dashboard_round(current_prod_metric) if current_prod_metric is not None else None,
            'baseline_metric': _dashboard_round(baseline_prod_metric) if baseline_prod_metric is not None else None,
            'baseline_litros_por_hora': _dashboard_round(fuel_baseline) if fuel_baseline else None,
            'desvio_produccion_pct': prod_diff,
            'desvio_combustible_pct': fuel_diff,
            'omite_metricas_horas': skips_hour_metrics,
            'estado': status,
        }
        finalized.append(result)

        label = f"{result['equipo']} - {result['tipo_operacion']} - {result['unidad_produccion']}"
        if fuel_severity in ('amarillo', 'rojo'):
            alertas.append({
                'tipo': 'combustible_alto',
                'severidad': fuel_severity,
                'entidad': label,
                'valor_actual': result['litros_por_hora'],
                'baseline': result['baseline_litros_por_hora'],
                'diferencia_pct': fuel_diff,
                'mensaje': f"{label} consume {fuel_diff}% más combustible por hora que su histórico comparable.",
                'segmento': result,
            })
        if prod_severity in ('amarillo', 'rojo'):
            alertas.append({
                'tipo': 'baja_produccion',
                'severidad': prod_severity,
                'entidad': label,
                'valor_actual': result['metric_value'],
                'baseline': result['baseline_metric'],
                'diferencia_pct': prod_diff,
                'mensaje': f"{label} está {prod_diff}% por debajo de su histórico comparable.",
                'segmento': result,
            })
        if horas == 0 and combustible > 0 and not skips_hour_metrics:
            alertas.append({
                'tipo': 'dato_inconsistente',
                'severidad': 'rojo',
                'entidad': label,
                'valor_actual': _dashboard_round(combustible),
                'baseline': None,
                'diferencia_pct': 0,
                'mensaje': f"{label} tiene combustible registrado sin horas comparables.",
                'segmento': result,
            })
        if horas == 0 and produccion > 0 and not is_hours and not skips_hour_metrics:
            alertas.append({
                'tipo': 'dato_inconsistente',
                'severidad': 'rojo',
                'entidad': label,
                'valor_actual': _dashboard_round(produccion),
                'baseline': None,
                'diferencia_pct': 0,
                'mensaje': f"{label} tiene producción registrada con horas cero.",
                'segmento': result,
            })
        if horas < 0 or produccion < 0:
            alertas.append({
                'tipo': 'dato_inconsistente',
                'severidad': 'rojo',
                'entidad': label,
                'valor_actual': _dashboard_round(horas if horas < 0 else produccion),
                'baseline': None,
                'diferencia_pct': 0,
                'mensaje': f"{label} tiene valores negativos que deben revisarse.",
                'segmento': result,
            })

    finalized.sort(key=lambda item: (
        {'rojo': 0, 'amarillo': 1, 'sin_historico': 2, 'verde': 3}.get(item['estado'], 4),
        item['unidad_negocio'],
        item['tipo_operacion'],
        item['unidad_produccion'],
        item['equipo'],
    ))
    alertas.sort(key=lambda item: (
        {'rojo': 0, 'amarillo': 1, 'sin_historico': 2, 'verde': 3}.get(item['severidad'], 4),
        -abs(float(item.get('diferencia_pct') or 0)),
    ))
    return finalized, alertas


def _dashboard_business_operation_key(segment):
    return (
        segment.get('unidad_negocio_id'),
        segment.get('tipo_operacion_id'),
        segment.get('unidad_produccion_id'),
    )


def _dashboard_aggregate_business_operation(segments):
    grouped = {}
    for segment in segments.values():
        key = _dashboard_business_operation_key(segment)
        item = grouped.setdefault(key, {
            'unidad_negocio_id': segment.get('unidad_negocio_id'),
            'unidad_negocio': segment.get('unidad_negocio'),
            'tipo_operacion_id': segment.get('tipo_operacion_id'),
            'tipo_operacion': segment.get('tipo_operacion'),
            'unidad_produccion_id': segment.get('unidad_produccion_id'),
            'unidad_produccion': segment.get('unidad_produccion'),
            'produccion': 0.0,
            'horas': 0.0,
            'combustible': 0.0,
            'registros': 0,
            'equipos': set(),
        })
        item['produccion'] += float(segment.get('produccion') or 0)
        item['horas'] += float(segment.get('horas') or 0)
        item['combustible'] += float(segment.get('combustible') or 0)
        item['registros'] += int(segment.get('registros') or 0)
        if segment.get('equipo_id'):
            item['equipos'].add(segment.get('equipo_id'))
    return grouped


def _dashboard_monthly_progress(base_qs, filters, anchor_date, months=6):
    current_start, current_end = _dashboard_mtd_window(anchor_date)
    current_qs = _dashboard_apply_filters(
        base_qs.filter(fecha__gte=current_start, fecha__lte=current_end),
        filters,
    )
    current_segments, _ = _dashboard_build_segments(current_qs, _dashboard_fuel_by_produccion(current_qs))
    current_grouped = _dashboard_aggregate_business_operation(current_segments)

    history_by_key = defaultdict(list)
    for offset in range(1, months + 1):
        hist_start, hist_end = _dashboard_mtd_window(anchor_date, offset)
        hist_qs = _dashboard_apply_filters(
            base_qs.filter(fecha__gte=hist_start, fecha__lte=hist_end),
            filters,
        )
        hist_segments, _ = _dashboard_build_segments(hist_qs, _dashboard_fuel_by_produccion(hist_qs))
        for key, item in _dashboard_aggregate_business_operation(hist_segments).items():
            history_by_key[key].append({
                'produccion': item['produccion'],
                'horas': item['horas'],
                'combustible': item['combustible'],
                'registros': item['registros'],
            })

    progress = []
    alertas = []
    for key, current in current_grouped.items():
        is_hours = _dashboard_is_hours_unit(current['unidad_produccion'])
        current_metric = current['horas'] if is_hours else current['produccion']
        metric_label = 'Horas MTD' if is_hours else f"{current['unidad_produccion']} MTD"
        samples = [
            sample['horas'] if is_hours else sample['produccion']
            for sample in history_by_key.get(key, [])
            if (sample['horas'] if is_hours else sample['produccion']) > 0
        ]
        expected = sum(samples) / len(samples) if samples else 0
        severity, diff = _dashboard_severity(current_metric, expected, 8, 15, direction='lower')
        if len(samples) < 2:
            severity, diff = 'sin_historico', 0

        item = {
            **{k: v for k, v in current.items() if k != 'equipos'},
            'equipos_activos': len(current['equipos']),
            'produccion': _dashboard_round(current['produccion']),
            'horas': _dashboard_round(current['horas']),
            'combustible': _dashboard_round(current['combustible']),
            'valor_actual': _dashboard_round(current_metric),
            'valor_esperado': _dashboard_round(expected),
            'diferencia_pct': diff,
            'meses_historicos': len(samples),
            'metric_label': metric_label,
            'estado': severity,
            'fecha_desde': current_start.isoformat(),
            'fecha_hasta': current_end.isoformat(),
        }
        progress.append(item)

        if severity in ('amarillo', 'rojo'):
            label = f"{item['unidad_negocio']} - {item['tipo_operacion']} - {item['unidad_produccion']}"
            alertas.append({
                'tipo': 'ritmo_mensual_bajo',
                'severidad': severity,
                'entidad': label,
                'valor_actual': item['valor_actual'],
                'baseline': item['valor_esperado'],
                'diferencia_pct': diff,
                'mensaje': f"{label} viene {diff}% por debajo del avance mensual esperado al dia {current_end.day}.",
                'segmento': item,
            })

    progress.sort(key=lambda item: (
        {'rojo': 0, 'amarillo': 1, 'sin_historico': 2, 'verde': 3}.get(item['estado'], 4),
        -abs(float(item.get('diferencia_pct') or 0)),
        item['unidad_negocio'],
        item['tipo_operacion'],
        item['unidad_produccion'],
    ))
    alertas.sort(key=lambda item: (
        {'rojo': 0, 'amarillo': 1}.get(item['severidad'], 2),
        -abs(float(item.get('diferencia_pct') or 0)),
    ))
    return progress, alertas


@login_required
@require_GET
def api_dashboard_ejecutivo(request):
    fecha_desde, fecha_hasta, error_response = _dashboard_dates(request)
    if error_response:
        return error_response

    filters = {
        'unidad_negocio_id': request.GET.get('unidad_negocio_id'),
        'tipo_operacion_id': request.GET.get('tipo_operacion_id'),
        'unidad_produccion_id': request.GET.get('unidad_produccion_id'),
        'equipo_id': request.GET.get('equipo_id'),
        'empleado_id': request.GET.get('empleado_id'),
    }

    base_qs = TableroProduccion.objects.select_related('unidad_negocio', 'tipo_operacion', 'unidad_produccion')

    qs_prod = base_qs.filter(
        fecha__gte=fecha_desde,
        fecha__lte=fecha_hasta,
    )
    qs_prod = _dashboard_apply_filters(qs_prod, filters)

    hist_desde = fecha_desde - timedelta(days=183)
    hist_hasta = fecha_desde - timedelta(days=1)
    qs_hist = TableroProduccion.objects.select_related('unidad_negocio', 'tipo_operacion', 'unidad_produccion').filter(
        fecha__gte=hist_desde,
        fecha__lte=hist_hasta,
    )
    qs_hist = _dashboard_apply_filters(qs_hist, filters)

    segments, daily = _dashboard_build_segments(qs_prod, _dashboard_fuel_by_produccion(qs_prod), include_daily=True)
    hist_segments, _ = _dashboard_build_segments(qs_hist, _dashboard_fuel_by_produccion(qs_hist))
    segmentos, alertas = _dashboard_finalize_segments(segments, hist_segments)
    avance_mensual, alertas_avance = _dashboard_monthly_progress(base_qs, filters, fecha_hasta)
    alertas = alertas + alertas_avance
    alertas.sort(key=lambda item: (
        {'rojo': 0, 'amarillo': 1, 'sin_historico': 2, 'verde': 3}.get(item['severidad'], 4),
        -abs(float(item.get('diferencia_pct') or 0)),
    ))

    produccion_por_unidad_map = defaultdict(lambda: {'unidad_produccion': '', 'produccion': 0.0, 'horas': 0.0, 'registros': 0})
    for segment in segmentos:
        item = produccion_por_unidad_map[segment['unidad_produccion_id']]
        item['unidad_produccion_id'] = segment['unidad_produccion_id']
        item['unidad_produccion'] = segment['unidad_produccion']
        item['produccion'] += segment['produccion']
        item['horas'] += segment['horas']
        item['registros'] += segment['registros']

    produccion_por_unidad = [
        {
            **item,
            'produccion': _dashboard_round(item['produccion']),
            'horas': _dashboard_round(item['horas']),
        }
        for item in produccion_por_unidad_map.values()
    ]
    produccion_por_unidad.sort(key=lambda item: item['unidad_produccion'])

    total_combustible = sum(item['combustible'] for item in segmentos)
    total_horas = sum(item['horas'] for item in segmentos)
    total_horas_no_operativas = sum(item['horas_no_operativas'] for item in segmentos)
    equipos_activos = len({item['equipo_id'] for item in segmentos if item.get('equipo_id')})
    rojas = sum(1 for item in alertas if item['severidad'] == 'rojo')
    amarillas = sum(1 for item in alertas if item['severidad'] == 'amarillo')

    estado_general = 'verde'
    if rojas:
        estado_general = 'rojo'
    elif amarillas:
        estado_general = 'amarillo'
    elif any(item['estado'] == 'sin_historico' for item in segmentos):
        estado_general = 'sin_historico'

    ranking_combustible = sorted(
        [item for item in segmentos if item.get('desvio_combustible_pct') is not None],
        key=lambda item: item.get('desvio_combustible_pct') or 0,
        reverse=True,
    )[:10]
    ranking_baja_produccion = sorted(
        [item for item in segmentos if item.get('desvio_produccion_pct') is not None],
        key=lambda item: item.get('desvio_produccion_pct') or 0,
        reverse=True,
    )[:10]
    ranking_no_operativas = sorted(segmentos, key=lambda item: item.get('horas_no_operativas') or 0, reverse=True)[:10]
    ranking_datos = [
        item for item in segmentos
        if item['horas'] <= 0 or item['produccion'] < 0 or item['estado'] == 'sin_historico'
    ][:10]
    ranking_avance_mensual = [
        item for item in avance_mensual
        if item['estado'] in ('rojo', 'amarillo')
    ][:10]

    fechas = sorted(daily.keys())
    series = {
        'fechas': fechas,
        'produccion': [_dashboard_round(daily[day]['produccion']) for day in fechas],
        'horas': [_dashboard_round(daily[day]['horas']) for day in fechas],
        'combustible': [_dashboard_round(daily[day]['combustible']) for day in fechas],
    }

    return JsonResponse({
        'periodo': {
            'fecha_desde': fecha_desde.isoformat(),
            'fecha_hasta': fecha_hasta.isoformat(),
            'historico_desde': hist_desde.isoformat(),
            'historico_hasta': hist_hasta.isoformat(),
        },
        'resumen_general': {
            'estado_general': estado_general,
            'combustible_total': _dashboard_round(total_combustible),
            'horas_operativas': _dashboard_round(total_horas),
            'horas_no_operativas': _dashboard_round(total_horas_no_operativas),
            'equipos_activos': equipos_activos,
            'registros': sum(item['registros'] for item in segmentos),
            'alertas_total': len(alertas),
            'alertas_rojas': rojas,
            'alertas_amarillas': amarillas,
            'segmentos_total': len(segmentos),
        },
        'produccion_por_unidad': produccion_por_unidad,
        'avance_mensual': avance_mensual,
        'segmentos': segmentos,
        'rankings': {
            'combustible': ranking_combustible,
            'baja_produccion': ranking_baja_produccion,
            'avance_mensual': ranking_avance_mensual,
            'horas_no_operativas': ranking_no_operativas,
            'datos_a_revisar': ranking_datos,
        },
        'alertas': alertas[:50],
        'series': series,
    })


@login_required
def api_consumo_por_equipo(request):
    """
    Devuelve consumo agregado por equipo en el rango/filtros dados.
    Response: {'data': [{ 'equipo_id', 'equipo', 'horas_trabajadas', 'litros', 'litros_por_hora' }, ... ]}
    Query params: fecha_desde, fecha_hasta, unidad_negocio_id, tipo_operacion_id, equipo_id, empleado_id
    """
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    unidad_negocio_id = request.GET.get('unidad_negocio_id')
    tipo_operacion_id = request.GET.get('tipo_operacion_id')
    equipo_id = request.GET.get('equipo_id')
    empleado_id = request.GET.get('empleado_id')

    # Filtrar movimientos de combustible y producciones por los mismos filtros
    qs_comb = MovimientoCombustible.objects.all()
    qs_prod = TableroProduccion.objects.all()

    if fecha_desde:
        qs_comb = qs_comb.filter(fecha__gte=fecha_desde)
        qs_prod = qs_prod.filter(fecha__gte=fecha_desde)
    if fecha_hasta:
        qs_comb = qs_comb.filter(fecha__lte=fecha_hasta)
        qs_prod = qs_prod.filter(fecha__lte=fecha_hasta)
    if unidad_negocio_id:
        qs_comb = qs_comb.filter(unidad_negocio_id=unidad_negocio_id)
        qs_prod = qs_prod.filter(unidad_negocio_id=unidad_negocio_id)
    if tipo_operacion_id:
        qs_prod = qs_prod.filter(tipo_operacion_id=tipo_operacion_id)
        # limitar movimientos a producciones ya filtradas (incluye fechas/unidad)
        prod_ids = qs_prod.values_list('id', flat=True)
        qs_comb = qs_comb.filter(idtabla__in=list(prod_ids))
    if equipo_id:
        qs_comb = qs_comb.filter(equipo_id=equipo_id)
        qs_prod = qs_prod.filter(equipo_id=equipo_id)
    if empleado_id:
        qs_prod = qs_prod.filter(empleado_id=empleado_id)
        prod_ids = qs_prod.values_list('id', flat=True)
        qs_comb = qs_comb.filter(idtabla__in=list(prod_ids))

    # Obtener ids de equipos relevantes
    equipo_ids_comb = list(qs_comb.values_list('equipo_id', flat=True).distinct())
    equipo_ids_prod = list(qs_prod.values_list('equipo_id', flat=True).distinct())
    equipo_ids = sorted(set([e for e in equipo_ids_comb + equipo_ids_prod if e is not None]))

    data = []
    for eid in equipo_ids:
        # nombre equipo
        try:
            equipo_obj = Equipo.objects.get(id=eid)
            equipo_nombre = equipo_obj.descripcion
        except Equipo.DoesNotExist:
            equipo_nombre = f'Equipo {eid}'

        # horas trabajadas desde producciones
        qs_e_prod = qs_prod.filter(equipo_id=eid).annotate(
            horas_trabajadas=ExpressionWrapper(F('hr_fin') - F('hr_inicio'), output_field=FloatField())
        )
        agg_h = qs_e_prod.aggregate(total_horas=Sum('horas_trabajadas'))
        total_horas = float(agg_h.get('total_horas') or 0)

        # litros consumidos desde movimientos
        agg_l = qs_comb.filter(equipo_id=eid).aggregate(total_litros=Sum('egreso'))
        total_litros = float(agg_l.get('total_litros') or 0)

        litros_por_hora = (total_litros / total_horas) if total_horas > 0 else 0

        data.append({
            'equipo_id': eid,
            'equipo': equipo_nombre,
            'horas_trabajadas': round(total_horas, 2),
            'litros': round(total_litros, 2),
            'litros_por_hora': round(litros_por_hora, 2),
        })

    return JsonResponse({'data': data})


@login_required
def api_unidades_negocio(request):
    """
    Devuelve la lista de unidades de negocio activas con id y descripción.
    Si se proporcionan fechas, filtra solo las unidades con actividad en ese rango.
    Query params: fecha_desde, fecha_hasta
    """
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    qs = UnidadNegocio.objects.filter(activo=True)
    
    if fecha_desde or fecha_hasta:
        produccion_qs = TableroProduccion.objects.all()
        if fecha_desde:
            produccion_qs = produccion_qs.filter(fecha__gte=fecha_desde)
        if fecha_hasta:
            produccion_qs = produccion_qs.filter(fecha__lte=fecha_hasta)
            
        unidades_activas_ids = produccion_qs.values_list('unidad_negocio_id', flat=True).distinct()
        qs = qs.filter(id__in=unidades_activas_ids)

    unidades = qs.values('id', 'descripcion').order_by('descripcion')
    return JsonResponse({'unidades': list(unidades)})


@login_required
def api_equipos_por_unidad(request):
    """
    Devuelve la lista de equipos que trabajaron en una unidad de negocio en un rango de fechas.
    Query params: unidad_negocio_id, fecha_desde, fecha_hasta
    """
    unidad_negocio_id = request.GET.get('unidad_negocio_id')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')

    if not unidad_negocio_id:
        return JsonResponse({'equipos': []})

    # Buscar equipos en producción
    qs = TableroProduccion.objects.filter(unidad_negocio_id=unidad_negocio_id)
    
    if fecha_desde:
        qs = qs.filter(fecha__gte=fecha_desde)
    if fecha_hasta:
        qs = qs.filter(fecha__lte=fecha_hasta)

    # Obtener IDs únicos de equipos
    equipo_ids = qs.values_list('equipo_id', flat=True).distinct()

    # Obtener información de los equipos
    equipos = Equipo.objects.filter(id__in=list(equipo_ids)).values('id', 'descripcion', 'patente').order_by('descripcion')

    return JsonResponse({'equipos': list(equipos)})


@login_required
def api_operadores_por_unidad(request):
    """
    Devuelve la lista de operadores (empleados) que trabajaron en una unidad de negocio en un rango de fechas.
    Query params: unidad_negocio_id, fecha_desde, fecha_hasta
    """
    unidad_negocio_id = request.GET.get('unidad_negocio_id')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')

    if not unidad_negocio_id:
        return JsonResponse({'operadores': []})

    qs = TableroProduccion.objects.filter(unidad_negocio_id=unidad_negocio_id)
    if fecha_desde:
        qs = qs.filter(fecha__gte=fecha_desde)
    if fecha_hasta:
        qs = qs.filter(fecha__lte=fecha_hasta)

    empleado_ids = list(qs.values_list('empleado_id', flat=True).distinct())

    # Usar el modelo Empleado para obtener nombre y apellido
    operadores = []
    if empleado_ids:
        from .models import Empleado
        empleados_qs = Empleado.objects.filter(id__in=[e for e in empleado_ids if e is not None])
        empleados_map = {e.id: f"{e.nombre} {e.apellido}" for e in empleados_qs}
        operadores = [{'id': e, 'nombre': empleados_map.get(e, f'Empleado {e}')} for e in empleado_ids if e is not None]

    return JsonResponse({'operadores': operadores})


@login_required
def api_tipos_operacion_por_unidad(request):
    """
    Devuelve la lista de tipos de operación que se usaron en una unidad de negocio en un rango de fechas.
    Query params: unidad_negocio_id, fecha_desde, fecha_hasta
    """
    unidad_negocio_id = request.GET.get('unidad_negocio_id')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')

    if not unidad_negocio_id:
        return JsonResponse({'tipos_operacion': []})

    # Buscar tipos de operación en producción
    qs = TableroProduccion.objects.filter(unidad_negocio_id=unidad_negocio_id)
    
    if fecha_desde:
        qs = qs.filter(fecha__gte=fecha_desde)
    if fecha_hasta:
        qs = qs.filter(fecha__lte=fecha_hasta)

    # Obtener IDs únicos de tipos de operación
    tipo_operacion_ids = qs.values_list('tipo_operacion_id', flat=True).distinct()

    # Obtener información de los tipos de operación
    tipos_operacion = TipoOperacion.objects.filter(id__in=list(tipo_operacion_ids)).values('id', 'descripcion').order_by('descripcion')

    return JsonResponse({'tipos_operacion': list(tipos_operacion)})


def _base_tipo_desde_unidad_produccion(descripcion):
    text = (descripcion or '').lower()
    if 'km' in text:
        return 'km'
    return 'hora'


def _movil_label(equipo):
    if not equipo:
        return ''
    patente = (equipo.patente or '').strip()
    if patente:
        return f"{equipo.descripcion} ({patente})"
    return equipo.descripcion


def _fila_con_ratios(row):
    prod_dia = float(row.get('prod_dia') or 0)
    prod_acum = float(row.get('prod_acum') or 0)
    litros_dia = float(row.get('litros_dia') or 0)
    litros_acum = float(row.get('litros_acum') or 0)
    horas_dia = float(row.get('horas_dia') or 0)
    horas_acum = float(row.get('horas_acum') or 0)

    row['consumo_dia'] = round((litros_dia / horas_dia) if horas_dia > 0 else 0, 2)
    row['consumo_acumulado'] = round((litros_acum / horas_acum) if horas_acum > 0 else 0, 2)
    row['prod_dia'] = round(prod_dia, 2)
    row['prod_acumulada'] = round(prod_acum, 2)
    row['total_litros'] = round(litros_acum, 2)
    row['total_produccion'] = round(prod_acum, 2)
    row['horas_dia'] = round(horas_dia, 2)
    row['horas_acum'] = round(horas_acum, 2)
    return row


def _build_reporte_produccion(mes_inicio, fecha_corte, unidad_negocio_id):
    qs_prod = (
        TableroProduccion.objects
        .select_related('unidad_negocio', 'unidad_produccion')
        .filter(
            fecha__gte=mes_inicio,
            fecha__lte=fecha_corte,
            unidad_negocio_id=unidad_negocio_id,
        )
        .order_by('unidad_negocio__descripcion', 'equipo_id')
    )

    litros_acc_por_equipo = defaultdict(float)
    litros_dia_por_equipo = defaultdict(float)

    movimientos_qs = MovimientoCombustible.objects.filter(
        fecha__gte=mes_inicio,
        fecha__lte=fecha_corte,
        unidad_negocio_id=unidad_negocio_id,
    )

    for item in (
        movimientos_qs
        .values('equipo_id')
        .annotate(total=Sum('egreso'))
    ):
        litros_acc_por_equipo[int(item['equipo_id'])] = float(item.get('total') or 0)

    for item in (
        movimientos_qs
        .filter(fecha=fecha_corte)
        .values('equipo_id')
        .annotate(total=Sum('egreso'))
    ):
        litros_dia_por_equipo[int(item['equipo_id'])] = float(item.get('total') or 0)

    filas = {}

    for prod in qs_prod:
        unidad_desc = prod.unidad_negocio.descripcion if prod.unidad_negocio else ''

        equipo_obj = None
        try:
            equipo_obj = Equipo.objects.get(id=prod.equipo_id)
        except Equipo.DoesNotExist:
            equipo_obj = None

        movil = _movil_label(equipo_obj) if equipo_obj else f'Equipo {prod.equipo_id}'
        key = (unidad_desc, prod.equipo_id, movil)

        if key not in filas:
            filas[key] = {
                'equipo_id': prod.equipo_id,
                'unidad_negocio_id': prod.unidad_negocio_id,
                'movil': movil,
                'un': unidad_desc,
                'litros_dia': 0.0,
                'litros_acum': 0.0,
                'prod_dia': 0.0,
                'prod_acum': 0.0,
                'horas_dia': 0.0,
                'horas_acum': 0.0,
            }

        fila = filas[key]
        prod_val = float(prod.produccion or 0)
        horas_val = float(prod.hr_fin or 0) - float(prod.hr_inicio or 0)
        fila['prod_acum'] += prod_val
        fila['horas_acum'] += horas_val
        fila['litros_acum'] += litros_acc_por_equipo.get(int(prod.equipo_id), 0)

        if prod.fecha == fecha_corte:
            fila['prod_dia'] += prod_val
            fila['horas_dia'] += horas_val
            fila['litros_dia'] += litros_dia_por_equipo.get(int(prod.equipo_id), 0)

    rows = list(filas.values())
    rows.sort(key=lambda r: ((r.get('un') or '').lower(), (r.get('movil') or '').lower()))
    rows = [_fila_con_ratios(r) for r in rows]

    subtotales_map = {}
    for r in rows:
        un_desc = r.get('un') or ''
        if un_desc not in subtotales_map:
            subtotales_map[un_desc] = {
                'equipo_id': None,
                'unidad_negocio_id': None,
                'movil': 'Subtotal',
                'un': un_desc,
                'litros_dia': 0.0,
                'litros_acum': 0.0,
                'prod_dia': 0.0,
                'prod_acum': 0.0,
                'horas_dia': 0.0,
                'horas_acum': 0.0,
            }
        subtotales_map[un_desc]['litros_dia'] += float(r.get('litros_dia') or 0)
        subtotales_map[un_desc]['litros_acum'] += float(r.get('litros_acum') or 0)
        subtotales_map[un_desc]['prod_dia'] += float(r.get('prod_dia') or 0)
        subtotales_map[un_desc]['prod_acum'] += float(r.get('prod_acumulada') or 0)
        subtotales_map[un_desc]['horas_dia'] += float(r.get('horas_dia') or 0)
        subtotales_map[un_desc]['horas_acum'] += float(r.get('horas_acum') or 0)

    subtotales = []
    for un_desc in sorted(subtotales_map.keys(), key=lambda x: (x or '').lower()):
        subtotales.append(_fila_con_ratios(subtotales_map[un_desc]))

    total_general = {
        'equipo_id': None,
        'unidad_negocio_id': None,
        'movil': 'Total General',
        'un': '-',
        'litros_dia': 0.0,
        'litros_acum': 0.0,
        'prod_dia': 0.0,
        'prod_acum': 0.0,
        'horas_dia': 0.0,
        'horas_acum': 0.0,
    }
    for r in rows:
        total_general['litros_dia'] += float(r.get('litros_dia') or 0)
        total_general['litros_acum'] += float(r.get('litros_acum') or 0)
        total_general['prod_dia'] += float(r.get('prod_dia') or 0)
        total_general['prod_acum'] += float(r.get('prod_acumulada') or 0)
        total_general['horas_dia'] += float(r.get('horas_dia') or 0)
        total_general['horas_acum'] += float(r.get('horas_acum') or 0)
    total_general = _fila_con_ratios(total_general)

    return {
        'meta': {
            'mes': mes_inicio.strftime('%Y-%m'),
            'fecha_corte': fecha_corte.isoformat(),
            'unidad_negocio_id': int(unidad_negocio_id),
        },
        'columnas': [
            'Movil',
            'UN',
            'Consumo Dia',
            'Consumo Acumulado',
            'Prod. Dia',
            'Prod. Acumulada',
            'Total Litros',
            'Total Produccion',
        ],
        'rows': rows,
        'subtotales_un': subtotales,
        'total_general': total_general,
    }


def _parse_reporte_request(request):
    mes = request.GET.get('mes')
    fecha_corte_raw = request.GET.get('fecha_corte')
    unidad_negocio_id = request.GET.get('unidad_negocio_id')

    if not mes or not fecha_corte_raw or not unidad_negocio_id:
        return None, JsonResponse({'detail': 'mes, fecha_corte y unidad_negocio_id son obligatorios'}, status=400)

    try:
        inicio_mes = datetime.strptime(f'{mes}-01', '%Y-%m-%d').date()
    except ValueError:
        return None, JsonResponse({'detail': 'mes debe tener formato YYYY-MM'}, status=400)

    try:
        fecha_corte = datetime.strptime(fecha_corte_raw, '%Y-%m-%d').date()
    except ValueError:
        return None, JsonResponse({'detail': 'fecha_corte debe tener formato YYYY-MM-DD'}, status=400)

    if inicio_mes.year != fecha_corte.year or inicio_mes.month != fecha_corte.month:
        return None, JsonResponse({'detail': 'fecha_corte debe pertenecer al mes seleccionado'}, status=400)

    try:
        int(unidad_negocio_id)
    except ValueError:
        return None, JsonResponse({'detail': 'unidad_negocio_id invalido'}, status=400)

    return (inicio_mes, fecha_corte, unidad_negocio_id), None


@login_required
def api_produccion_reporte(request):
    parsed, error_response = _parse_reporte_request(request)
    if error_response:
        return error_response

    inicio_mes, fecha_corte, unidad_negocio_id = parsed
    payload = _build_reporte_produccion(inicio_mes, fecha_corte, unidad_negocio_id)
    return JsonResponse(payload)


@login_required
def api_produccion_reporte_export_excel(request):
    parsed, error_response = _parse_reporte_request(request)
    if error_response:
        return error_response

    inicio_mes, fecha_corte, unidad_negocio_id = parsed
    payload = _build_reporte_produccion(inicio_mes, fecha_corte, unidad_negocio_id)

    wb = Workbook()
    ws = wb.active
    ws.title = 'Produccion'

    header_fill = PatternFill(start_color='22C55E', end_color='22C55E', fill_type='solid')
    header_font = Font(bold=True, color='FFFFFF')
    header_alignment = Alignment(horizontal='center', vertical='center')

    headers = payload.get('columnas', [])
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_alignment

    row_num = 2
    for fila in payload.get('rows', []):
        ws.cell(row=row_num, column=1, value=fila.get('movil', ''))
        ws.cell(row=row_num, column=2, value=fila.get('un', ''))
        ws.cell(row=row_num, column=3, value=fila.get('consumo_dia', 0))
        ws.cell(row=row_num, column=4, value=fila.get('consumo_acumulado', 0))
        ws.cell(row=row_num, column=5, value=fila.get('prod_dia', 0))
        ws.cell(row=row_num, column=6, value=fila.get('prod_acumulada', 0))
        ws.cell(row=row_num, column=7, value=fila.get('total_litros', 0))
        ws.cell(row=row_num, column=8, value=fila.get('total_produccion', 0))
        row_num += 1

    for fila in payload.get('subtotales_un', []):
        ws.cell(row=row_num, column=1, value=fila.get('movil', 'Subtotal'))
        ws.cell(row=row_num, column=2, value=fila.get('un', ''))
        ws.cell(row=row_num, column=3, value=fila.get('consumo_dia', 0))
        ws.cell(row=row_num, column=4, value=fila.get('consumo_acumulado', 0))
        ws.cell(row=row_num, column=5, value=fila.get('prod_dia', 0))
        ws.cell(row=row_num, column=6, value=fila.get('prod_acumulada', 0))
        ws.cell(row=row_num, column=7, value=fila.get('total_litros', 0))
        ws.cell(row=row_num, column=8, value=fila.get('total_produccion', 0))
        for col in range(1, 9):
            ws.cell(row=row_num, column=col).font = Font(bold=True)
        row_num += 1

    total = payload.get('total_general', {})
    ws.cell(row=row_num, column=1, value=total.get('movil', 'Total General'))
    ws.cell(row=row_num, column=2, value=total.get('un', '-'))
    ws.cell(row=row_num, column=3, value=total.get('consumo_dia', 0))
    ws.cell(row=row_num, column=4, value=total.get('consumo_acumulado', 0))
    ws.cell(row=row_num, column=5, value=total.get('prod_dia', 0))
    ws.cell(row=row_num, column=6, value=total.get('prod_acumulada', 0))
    ws.cell(row=row_num, column=7, value=total.get('total_litros', 0))
    ws.cell(row=row_num, column=8, value=total.get('total_produccion', 0))
    for col in range(1, 9):
        ws.cell(row=row_num, column=col).font = Font(bold=True)

    for col_num in range(1, 9):
        ws.column_dimensions[get_column_letter(col_num)].width = 20

    filename = f"produccion_{fecha_corte.strftime('%Y_%m_%d')}.xlsx"
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename={filename}'
    wb.save(response)
    return response


@login_required
def api_produccion_detalle(request):
    """
    Devuelve el detalle de todos los registros de producción.
    Query params: fecha_desde, fecha_hasta, unidad_negocio_id, tipo_operacion_id,
    unidad_produccion_id, equipo_id, page, page_size
    """
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    unidad_negocio_id = request.GET.get('unidad_negocio_id')
    tipo_operacion_id = request.GET.get('tipo_operacion_id')
    unidad_produccion_id = request.GET.get('unidad_produccion_id')
    equipo_id = request.GET.get('equipo_id')
    page_number = request.GET.get('page', 1)
    page_size = request.GET.get('page_size', 10)

    # Filtrar producciones
    qs = TableroProduccion.objects.select_related('unidad_negocio', 'unidad_produccion').all()

    if fecha_desde:
        qs = qs.filter(fecha__gte=fecha_desde)
    if fecha_hasta:
        qs = qs.filter(fecha__lte=fecha_hasta)
    if unidad_negocio_id:
        qs = qs.filter(unidad_negocio_id=unidad_negocio_id)
    if tipo_operacion_id:
        qs = qs.filter(tipo_operacion_id=tipo_operacion_id)
    if unidad_produccion_id:
        qs = qs.filter(unidad_produccion_id=unidad_produccion_id)
    if equipo_id:
        qs = qs.filter(equipo_id=equipo_id)

    qs = qs.order_by('-fecha', '-id')

    paginator = Paginator(qs, page_size)
    page_obj = paginator.get_page(page_number)

    detalle = []
    for prod in page_obj:
        # Buscar equipo
        try:
            equipo = Equipo.objects.get(id=prod.equipo_id)
            equipo_desc = equipo.descripcion
            equipo_patente = equipo.patente or ''
        except Equipo.DoesNotExist:
            equipo_desc = f'Equipo {prod.equipo_id}'
            equipo_patente = ''

        # Obtener descripción de unidad de producción desde la relación ForeignKey
        unidad_prod_desc = prod.unidad_produccion.descripcion if prod.unidad_produccion else ''

        horas_trabajadas = round(float(prod.hr_fin - prod.hr_inicio), 2)

        detalle.append({
            'id': prod.id,
            'fecha': prod.fecha.isoformat() if prod.fecha else None,
            'unidad_negocio': prod.unidad_negocio.descripcion if prod.unidad_negocio else '',
            'equipo': equipo_desc,
            'patente': equipo_patente,
            'hr_inicio': round(float(prod.hr_inicio), 2),
            'hr_fin': round(float(prod.hr_fin), 2),
            'horas_trabajadas': horas_trabajadas,
            'produccion': round(float(prod.produccion or 0), 2),
            'unidad_produccion': unidad_prod_desc,
            'turno': prod.turno or '',
            'observaciones': prod.observaciones or '',
        })

    return JsonResponse({
        'detalle': detalle,
        'total_pages': paginator.num_pages,
        'current_page': page_obj.number,
        'total_items': paginator.count,
    })


@login_required
@require_http_methods(["DELETE"])
def api_produccion_delete(request, produccion_id):
    try:
        with transaction.atomic():
            produccion = TableroProduccion.objects.get(id=produccion_id)
            combustible_eliminados, _ = MovimientoCombustible.objects.filter(idtabla=produccion.id).delete()
            produccion.delete()
    except TableroProduccion.DoesNotExist:
        return JsonResponse({'detail': 'Movimiento no encontrado'}, status=404)

    return JsonResponse({
        'detail': 'Movimiento eliminado',
        'produccion_id': produccion_id,
        'combustible_eliminados': combustible_eliminados,
    })


@login_required
def api_combustible_data(request):
    """
    Devuelve datos de consumo de combustible.
    Muestra TODO el combustible (no solo producción).
    Query params: fecha_desde, fecha_hasta, unidad_negocio_id, tipo_operacion_id, equipo_id
    """
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    unidad_negocio_id = request.GET.get('unidad_negocio_id')
    tipo_operacion_id = request.GET.get('tipo_operacion_id')
    equipo_id = request.GET.get('equipo_id')
    empleado_id = request.GET.get('empleado_id')

    # Filtrar movimientos de combustible (TODOS, no solo producción)
    qs = MovimientoCombustible.objects.all()

    if fecha_desde:
        qs = qs.filter(fecha__gte=fecha_desde)
    if fecha_hasta:
        qs = qs.filter(fecha__lte=fecha_hasta)
    if unidad_negocio_id:
        qs = qs.filter(unidad_negocio_id=unidad_negocio_id)
    if equipo_id:
        qs = qs.filter(equipo_id=equipo_id)
    
    # Si hay filtro de tipo_operacion, filtrar por idtabla de producciones que cumplan ese tipo
    if tipo_operacion_id:
        qs_prod = TableroProduccion.objects.filter(tipo_operacion_id=tipo_operacion_id)
        if empleado_id:
            qs_prod = qs_prod.filter(empleado_id=empleado_id)
        producciones_ids = qs_prod.values_list('id', flat=True)
        qs = qs.filter(idtabla__in=list(producciones_ids))
    elif empleado_id:
        # Si se filtró por empleado sin tipo_operacion, filtrar movimientos por producciones del empleado
        producciones_ids = TableroProduccion.objects.filter(empleado_id=empleado_id).values_list('id', flat=True)
        qs = qs.filter(idtabla__in=list(producciones_ids))

    # Agrupar por fecha y sumar egresos (consumo)
    data_por_fecha = qs.values('fecha').annotate(
        total_consumo=Sum('egreso')
    ).order_by('fecha')

    data = []
    for item in data_por_fecha:
        data.append({
            'fecha': item['fecha'].isoformat() if item['fecha'] else None,
            'total_consumo': round(float(item['total_consumo'] or 0), 2)
        })

    return JsonResponse({'data': data})


@login_required
def api_combustible_kpis(request):
    """
    Devuelve KPIs de combustible relacionados con producción.
    Query params: fecha_desde, fecha_hasta, unidad_negocio_id, tipo_operacion_id, equipo_id
    KPIs: total_combustible, consumo_por_hora (litros / horas)
    """
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    unidad_negocio_id = request.GET.get('unidad_negocio_id')
    tipo_operacion_id = request.GET.get('tipo_operacion_id')
    equipo_id = request.GET.get('equipo_id')
    empleado_id = request.GET.get('empleado_id')

    # Filtrar movimientos de combustible (TODOS, no solo producción)
    qs_combustible = MovimientoCombustible.objects.all()

    if fecha_desde:
        qs_combustible = qs_combustible.filter(fecha__gte=fecha_desde)
    if fecha_hasta:
        qs_combustible = qs_combustible.filter(fecha__lte=fecha_hasta)
    if unidad_negocio_id:
        qs_combustible = qs_combustible.filter(unidad_negocio_id=unidad_negocio_id)
    if equipo_id:
        qs_combustible = qs_combustible.filter(equipo_id=equipo_id)
    
    # Si hay filtro de tipo_operacion, filtrar por idtabla de producciones que cumplan ese tipo
    if tipo_operacion_id:
        qs_prod = TableroProduccion.objects.filter(tipo_operacion_id=tipo_operacion_id)
        if empleado_id:
            qs_prod = qs_prod.filter(empleado_id=empleado_id)
        producciones_ids = qs_prod.values_list('id', flat=True)
        qs_combustible = qs_combustible.filter(idtabla__in=list(producciones_ids))
    elif empleado_id:
        producciones_ids = TableroProduccion.objects.filter(empleado_id=empleado_id).values_list('id', flat=True)
        qs_combustible = qs_combustible.filter(idtabla__in=list(producciones_ids))

    # Total de combustible consumido (egreso)
    agg_combustible = qs_combustible.aggregate(total_combustible=Sum('egreso'))
    total_combustible = float(agg_combustible.get('total_combustible') or 0)

    # Calcular horas de producción con los mismos filtros de fecha y unidad de negocio
    qs_produccion = TableroProduccion.objects.all()
    
    if fecha_desde:
        qs_produccion = qs_produccion.filter(fecha__gte=fecha_desde)
    if fecha_hasta:
        qs_produccion = qs_produccion.filter(fecha__lte=fecha_hasta)
    if unidad_negocio_id:
        qs_produccion = qs_produccion.filter(unidad_negocio_id=unidad_negocio_id)
    if tipo_operacion_id:
        qs_produccion = qs_produccion.filter(tipo_operacion_id=tipo_operacion_id)
    if equipo_id:
        qs_produccion = qs_produccion.filter(equipo_id=equipo_id)
    if empleado_id:
        qs_produccion = qs_produccion.filter(empleado_id=empleado_id)

    # Calcular total de horas trabajadas (hr_fin - hr_inicio)
    qs_produccion = qs_produccion.annotate(
        horas_trabajadas=ExpressionWrapper(
            F('hr_fin') - F('hr_inicio'),
            output_field=FloatField()
        )
    )
    agg_horas = qs_produccion.aggregate(total_horas=Sum('horas_trabajadas'))
    total_horas = float(agg_horas.get('total_horas') or 0)

    # Calcular consumo por hora (litros / horas)
    consumo_por_hora = (total_combustible / total_horas) if total_horas > 0 else 0

    result = {
        'total_combustible': round(total_combustible, 2),
        'horas_por_litro': round(consumo_por_hora, 2),
        'total_horas': round(total_horas, 2),
    }

    return JsonResponse({'kpis': result})


@login_required
def api_combustible_detalle(request):
    """
    Devuelve el detalle de todos los movimientos de combustible relacionados con producción.
    Query params: fecha_desde, fecha_hasta, unidad_negocio_id, tipo_operacion_id,
    unidad_produccion_id, equipo_id, page, page_size
    """
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    unidad_negocio_id = request.GET.get('unidad_negocio_id')
    tipo_operacion_id = request.GET.get('tipo_operacion_id')
    unidad_produccion_id = request.GET.get('unidad_produccion_id')
    equipo_id = request.GET.get('equipo_id')
    empleado_id = request.GET.get('empleado_id')
    page_number = request.GET.get('page', 1)
    page_size = request.GET.get('page_size', 10)

    # Filtrar movimientos de combustible relacionados con producción
    qs = MovimientoCombustible.objects.select_related(
        'equipo', 'tipo_combustible', 'unidad_negocio'
    )

    if fecha_desde:
        qs = qs.filter(fecha__gte=fecha_desde)
    if fecha_hasta:
        qs = qs.filter(fecha__lte=fecha_hasta)
    if unidad_negocio_id:
        qs = qs.filter(unidad_negocio_id=unidad_negocio_id)
    if equipo_id:
        qs = qs.filter(equipo_id=equipo_id)
    
    # Si hay filtros de producción, filtrar por idtabla de producciones comparables.
    if tipo_operacion_id or unidad_produccion_id:
        qs_prod = TableroProduccion.objects.all()
        if tipo_operacion_id:
            qs_prod = qs_prod.filter(tipo_operacion_id=tipo_operacion_id)
        if unidad_produccion_id:
            qs_prod = qs_prod.filter(unidad_produccion_id=unidad_produccion_id)
        if empleado_id:
            qs_prod = qs_prod.filter(empleado_id=empleado_id)
        producciones_ids = qs_prod.values_list('id', flat=True)
        qs = qs.filter(idtabla__in=list(producciones_ids))
    elif empleado_id:
        producciones_ids = TableroProduccion.objects.filter(empleado_id=empleado_id).values_list('id', flat=True)
        qs = qs.filter(idtabla__in=list(producciones_ids))

    qs = qs.order_by('-fecha', '-id')

    paginator = Paginator(qs, page_size)
    page_obj = paginator.get_page(page_number)

    detalle = []
    for mov in page_obj:
        detalle.append({
            'id': mov.id,
            'fecha': mov.fecha.isoformat() if mov.fecha else None,
            'equipo': mov.equipo.descripcion if mov.equipo else '',
            'tipo_combustible': mov.tipo_combustible.descripcion if mov.tipo_combustible else '',
            'unidad_negocio': mov.unidad_negocio.descripcion if mov.unidad_negocio else '',
            'egreso': round(float(mov.egreso or 0), 2),
            'km_hora': round(float(mov.km_hora or 0), 2),
            'precio_litro': round(float(mov.precio_litro or 0), 2),
            'remito': mov.remito or '',
            'observaciones': mov.observaciones or '',
            'idtabla': mov.idtabla,
        })

    return JsonResponse({
        'detalle': detalle,
        'total_pages': paginator.num_pages,
        'current_page': page_obj.number,
        'total_items': paginator.count,
    })


@login_required
def api_produccion_export_excel(request):
    """
    Exporta todos los registros de producción a Excel.
    Query params: fecha_desde, fecha_hasta, unidad_negocio_id, tipo_operacion_id, equipo_id
    """
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    unidad_negocio_id = request.GET.get('unidad_negocio_id')
    tipo_operacion_id = request.GET.get('tipo_operacion_id')
    equipo_id = request.GET.get('equipo_id')
    empleado_id = request.GET.get('empleado_id')

    # Filtrar producciones
    qs = TableroProduccion.objects.select_related('unidad_negocio', 'unidad_produccion').all()

    if fecha_desde:
        qs = qs.filter(fecha__gte=fecha_desde)
    if fecha_hasta:
        qs = qs.filter(fecha__lte=fecha_hasta)
    if unidad_negocio_id:
        qs = qs.filter(unidad_negocio_id=unidad_negocio_id)
    if tipo_operacion_id:
        qs = qs.filter(tipo_operacion_id=tipo_operacion_id)
    if equipo_id:
        qs = qs.filter(equipo_id=equipo_id)
    if empleado_id:
        qs = qs.filter(empleado_id=empleado_id)

    qs = qs.order_by('-fecha', '-id')

    # Crear workbook
    wb = Workbook()
    ws = wb.active
    ws.title = 'Producción'

    # Estilos
    header_fill = PatternFill(start_color='22C55E', end_color='22C55E', fill_type='solid')
    header_font = Font(bold=True, color='FFFFFF')
    header_alignment = Alignment(horizontal='center', vertical='center')

    # Encabezados
    headers = ['Fecha', 'Unidad Negocio', 'Equipo', 'Patente', 'Hr Inicio', 'Hr Fin', 'Horas', 'Producción', 'Unidad Prod.', 'Turno', 'Observaciones']
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num)
        cell.value = header
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_alignment

    # Datos
    row_num = 2
    for prod in qs:
        # Buscar equipo
        try:
            equipo = Equipo.objects.get(id=prod.equipo_id)
            equipo_desc = equipo.descripcion
            equipo_patente = equipo.patente or ''
        except Equipo.DoesNotExist:
            equipo_desc = f'Equipo {prod.equipo_id}'
            equipo_patente = ''

        unidad_prod_desc = prod.unidad_produccion.descripcion if prod.unidad_produccion else ''
        horas_trabajadas = round(float(prod.hr_fin - prod.hr_inicio), 2)

        ws.cell(row=row_num, column=1, value=prod.fecha.isoformat() if prod.fecha else '')
        ws.cell(row=row_num, column=2, value=prod.unidad_negocio.descripcion if prod.unidad_negocio else '')
        ws.cell(row=row_num, column=3, value=equipo_desc)
        ws.cell(row=row_num, column=4, value=equipo_patente)
        ws.cell(row=row_num, column=5, value=round(float(prod.hr_inicio), 2))
        ws.cell(row=row_num, column=6, value=round(float(prod.hr_fin), 2))
        ws.cell(row=row_num, column=7, value=horas_trabajadas)
        ws.cell(row=row_num, column=8, value=round(float(prod.produccion or 0), 2))
        ws.cell(row=row_num, column=9, value=unidad_prod_desc)
        ws.cell(row=row_num, column=10, value=prod.turno or '')
        ws.cell(row=row_num, column=11, value=prod.observaciones or '')
        row_num += 1

    # Ajustar ancho de columnas
    for col_num in range(1, len(headers) + 1):
        column_letter = get_column_letter(col_num)
        ws.column_dimensions[column_letter].width = 15

    # Crear respuesta HTTP
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=produccion_export.xlsx'
    wb.save(response)
    return response


@login_required
def api_enviar_informe_email(request):
    """
    Envia por email un resumen de KPIs en formato HTML.
    Espera JSON (POST) con: to (email destinatario) y opcionalmente los mismos filtros usados en otros endpoints:
    fecha_desde, fecha_hasta, unidad_negocio_id, tipo_operacion_id, equipo_id, empleado_id
    """
    if request.method != 'POST':
        return JsonResponse({'detail': 'Method not allowed'}, status=405)

    try:
        payload = json.loads(request.body.decode())
    except Exception:
        return JsonResponse({'detail': 'Invalid JSON'}, status=400)

    to_email = payload.get('to')
    if not to_email:
        return JsonResponse({'detail': 'Missing "to" email address'}, status=400)

    # Extract filters
    fecha_desde = payload.get('fecha_desde')
    fecha_hasta = payload.get('fecha_hasta')
    unidad_negocio_id = payload.get('unidad_negocio_id')
    tipo_operacion_id = payload.get('tipo_operacion_id')
    equipo_id = payload.get('equipo_id')
    empleado_id = payload.get('empleado_id')

    # Reuse logic from api_produccion_kpis and api_combustible_kpis to compute KPIs
    qs = TableroProduccion.objects.all()
    if fecha_desde:
        qs = qs.filter(fecha__gte=fecha_desde)
    if fecha_hasta:
        qs = qs.filter(fecha__lte=fecha_hasta)
    if unidad_negocio_id:
        qs = qs.filter(unidad_negocio_id=unidad_negocio_id)
    if tipo_operacion_id:
        qs = qs.filter(tipo_operacion_id=tipo_operacion_id)
    if equipo_id:
        qs = qs.filter(equipo_id=equipo_id)
    if empleado_id:
        qs = qs.filter(empleado_id=empleado_id)

    qs = qs.annotate(
        horas_trabajadas=ExpressionWrapper(
            F('hr_fin') - F('hr_inicio'),
            output_field=FloatField()
        )
    )

    agg = qs.aggregate(
        total_horas=Sum('horas_trabajadas'),
        total_produccion=Sum('produccion'),
        entradas=Sum(ExpressionWrapper(F('id') * 0 + 1, output_field=FloatField())),
        horas_no_operativas=Sum('hrs_no_operativas')
    )

    total_horas = float(agg.get('total_horas') or 0)
    total_produccion = float(agg.get('total_produccion') or 0)
    entradas = int(agg.get('entradas') or 0)
    horas_no_operativas = float(agg.get('horas_no_operativas') or 0)
    avg_production_per_hour = (total_produccion / total_horas) if total_horas > 0 else 0
    eficiencia = ((total_horas - horas_no_operativas) / total_horas * 100) if total_horas > 0 else 0

    # Combustible KPIs
    qs_combustible = MovimientoCombustible.objects.all()
    if fecha_desde:
        qs_combustible = qs_combustible.filter(fecha__gte=fecha_desde)
    if fecha_hasta:
        qs_combustible = qs_combustible.filter(fecha__lte=fecha_hasta)
    if unidad_negocio_id:
        qs_combustible = qs_combustible.filter(unidad_negocio_id=unidad_negocio_id)
    if equipo_id:
        qs_combustible = qs_combustible.filter(equipo_id=equipo_id)
    if tipo_operacion_id:
        qs_prod = TableroProduccion.objects.filter(tipo_operacion_id=tipo_operacion_id)
        if empleado_id:
            qs_prod = qs_prod.filter(empleado_id=empleado_id)
        producciones_ids = qs_prod.values_list('id', flat=True)
        qs_combustible = qs_combustible.filter(idtabla__in=list(producciones_ids))
    elif empleado_id:
        producciones_ids = TableroProduccion.objects.filter(empleado_id=empleado_id).values_list('id', flat=True)
        qs_combustible = qs_combustible.filter(idtabla__in=list(producciones_ids))

    agg_combustible = qs_combustible.aggregate(total_combustible=Sum('egreso'))
    total_combustible = float(agg_combustible.get('total_combustible') or 0)
    # horas para combustible
    qs_produccion_for_comb = TableroProduccion.objects.all()
    if fecha_desde:
        qs_produccion_for_comb = qs_produccion_for_comb.filter(fecha__gte=fecha_desde)
    if fecha_hasta:
        qs_produccion_for_comb = qs_produccion_for_comb.filter(fecha__lte=fecha_hasta)
    if unidad_negocio_id:
        qs_produccion_for_comb = qs_produccion_for_comb.filter(unidad_negocio_id=unidad_negocio_id)
    if tipo_operacion_id:
        qs_produccion_for_comb = qs_produccion_for_comb.filter(tipo_operacion_id=tipo_operacion_id)
    if equipo_id:
        qs_produccion_for_comb = qs_produccion_for_comb.filter(equipo_id=equipo_id)
    if empleado_id:
        qs_produccion_for_comb = qs_produccion_for_comb.filter(empleado_id=empleado_id)
    qs_produccion_for_comb = qs_produccion_for_comb.annotate(
        horas_trabajadas=ExpressionWrapper(
            F('hr_fin') - F('hr_inicio'),
            output_field=FloatField()
        )
    )
    agg_horas_comb = qs_produccion_for_comb.aggregate(total_horas=Sum('horas_trabajadas'))
    horas_para_combustible = float(agg_horas_comb.get('total_horas') or 0)
    consumo_por_hora = (total_combustible / horas_para_combustible) if horas_para_combustible > 0 else 0

    # Construir HTML
    html = f"""
    <html>
    <body>
      <h2>Informe de KPIs</h2>
      <table border="0" cellpadding="6" style="border-collapse:collapse;">
        <tr><td><strong>Total Horas</strong></td><td>{round(total_horas,2)}</td></tr>
        <tr><td><strong>Horas No Operativas</strong></td><td>{round(horas_no_operativas,2)}</td></tr>
        <tr><td><strong>Eficiencia (%)</strong></td><td>{round(eficiencia,2)}</td></tr>
        <tr><td><strong>Total Producción</strong></td><td>{round(total_produccion,2)}</td></tr>
        <tr><td><strong>Prod / Hora</strong></td><td>{round(avg_production_per_hour,2)}</td></tr>
        <tr><td><strong>Total Combustible (L)</strong></td><td>{round(total_combustible,2)}</td></tr>
        <tr><td><strong>Consumo (L/h)</strong></td><td>{round(consumo_por_hora,2)}</td></tr>
      </table>
    </body>
    </html>
    """

    try:
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or getattr(settings, 'EMAIL_HOST_USER', None) or 'no-reply@example.com'
        msg = EmailMessage(subject='Informe de KPIs', body=html, from_email=from_email, to=[to_email])
        msg.content_subtype = 'html'
        msg.send(fail_silently=False)
    except Exception as e:
        return JsonResponse({'detail': 'Error sending email', 'error': str(e)}, status=500)

    return JsonResponse({'detail': 'Email sent'})


@login_required
def api_combustible_export_excel(request):
    """
    Exporta todos los registros de combustible a Excel.
    Query params: fecha_desde, fecha_hasta, unidad_negocio_id, tipo_operacion_id, equipo_id
    """
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    unidad_negocio_id = request.GET.get('unidad_negocio_id')
    tipo_operacion_id = request.GET.get('tipo_operacion_id')
    equipo_id = request.GET.get('equipo_id')
    empleado_id = request.GET.get('empleado_id')

    # Filtrar movimientos de combustible
    qs = MovimientoCombustible.objects.select_related(
        'equipo', 'tipo_combustible', 'unidad_negocio'
    )

    if fecha_desde:
        qs = qs.filter(fecha__gte=fecha_desde)
    if fecha_hasta:
        qs = qs.filter(fecha__lte=fecha_hasta)
    if unidad_negocio_id:
        qs = qs.filter(unidad_negocio_id=unidad_negocio_id)
    if equipo_id:
        qs = qs.filter(equipo_id=equipo_id)
    
    if tipo_operacion_id:
        qs_prod = TableroProduccion.objects.filter(tipo_operacion_id=tipo_operacion_id)
        if empleado_id:
            qs_prod = qs_prod.filter(empleado_id=empleado_id)
        producciones_ids = qs_prod.values_list('id', flat=True)
        qs = qs.filter(idtabla__in=list(producciones_ids))
    elif empleado_id:
        producciones_ids = TableroProduccion.objects.filter(empleado_id=empleado_id).values_list('id', flat=True)
        qs = qs.filter(idtabla__in=list(producciones_ids))

    qs = qs.order_by('-fecha', '-id')

    # Crear workbook
    wb = Workbook()
    ws = wb.active
    ws.title = 'Combustible'

    # Estilos
    header_fill = PatternFill(start_color='F59E0B', end_color='F59E0B', fill_type='solid')
    header_font = Font(bold=True, color='FFFFFF')
    header_alignment = Alignment(horizontal='center', vertical='center')

    # Encabezados
    headers = ['Fecha', 'Equipo', 'Tipo Combustible', 'Unidad Negocio', 'Litros', 'Km/Hora', 'Precio/Litro', 'Remito', 'Observaciones']
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num)
        cell.value = header
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_alignment

    # Datos
    row_num = 2
    for mov in qs:
        ws.cell(row=row_num, column=1, value=mov.fecha.isoformat() if mov.fecha else '')
        ws.cell(row=row_num, column=2, value=mov.equipo.descripcion if mov.equipo else '')
        ws.cell(row=row_num, column=3, value=mov.tipo_combustible.descripcion if mov.tipo_combustible else '')
        ws.cell(row=row_num, column=4, value=mov.unidad_negocio.descripcion if mov.unidad_negocio else '')
        ws.cell(row=row_num, column=5, value=round(float(mov.egreso or 0), 2))
        ws.cell(row=row_num, column=6, value=round(float(mov.km_hora or 0), 2))
        ws.cell(row=row_num, column=7, value=round(float(mov.precio_litro or 0), 2))
        ws.cell(row=row_num, column=8, value=mov.remito or '')
        ws.cell(row=row_num, column=9, value=mov.observaciones or '')
        row_num += 1

    # Ajustar ancho de columnas
    for col_num in range(1, len(headers) + 1):
        column_letter = get_column_letter(col_num)
        ws.column_dimensions[column_letter].width = 15

    # Crear respuesta HTTP
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=combustible_export.xlsx'
    wb.save(response)
    return response


@login_required
def api_combustible_consumo_por_hora(request):
    """
    Calcula el consumo por hora diario por equipo.
    Consumo por hora = litros del dia / sum(hr_fin - hr_inicio) del dia.
    Query params: fecha_desde, fecha_hasta, unidad_negocio_id, tipo_operacion_id,
    equipo_id, empleado_id
    """
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    unidad_negocio_id = request.GET.get('unidad_negocio_id')
    tipo_operacion_id = request.GET.get('tipo_operacion_id')
    unidad_produccion_id = request.GET.get('unidad_produccion_id')
    equipo_id = request.GET.get('equipo_id')
    empleado_id = request.GET.get('empleado_id')

    qs_prod = TableroProduccion.objects.all()
    qs_comb = MovimientoCombustible.objects.all()

    if fecha_desde:
        qs_prod = qs_prod.filter(fecha__gte=fecha_desde)
        qs_comb = qs_comb.filter(fecha__gte=fecha_desde)
    if fecha_hasta:
        qs_prod = qs_prod.filter(fecha__lte=fecha_hasta)
        qs_comb = qs_comb.filter(fecha__lte=fecha_hasta)
    if unidad_negocio_id:
        qs_prod = qs_prod.filter(unidad_negocio_id=unidad_negocio_id)
        qs_comb = qs_comb.filter(unidad_negocio_id=unidad_negocio_id)
    if tipo_operacion_id:
        qs_prod = qs_prod.filter(tipo_operacion_id=tipo_operacion_id)
    if equipo_id:
        qs_prod = qs_prod.filter(equipo_id=equipo_id)
        qs_comb = qs_comb.filter(equipo_id=equipo_id)
    if empleado_id:
        qs_prod = qs_prod.filter(empleado_id=empleado_id)

    if tipo_operacion_id or empleado_id:
        producciones_ids = list(qs_prod.values_list('id', flat=True))
        qs_comb = qs_comb.filter(idtabla__in=producciones_ids)

    prod_data = (
        qs_prod.annotate(
            horas_trabajadas=ExpressionWrapper(
                F('hr_fin') - F('hr_inicio'),
                output_field=FloatField()
            )
        )
        .values('fecha', 'equipo_id')
        .annotate(total_horas=Sum('horas_trabajadas'))
    )

    horas_por_dia_equipo = {
        (row['fecha'], row['equipo_id']): float(row['total_horas'] or 0)
        for row in prod_data
    }

    fuel_data = (
        qs_comb.values('fecha', 'equipo_id')
        .annotate(total_litros=Sum('egreso'))
        .order_by('fecha', 'equipo_id')
    )

    equipo_ids = {row['equipo_id'] for row in fuel_data if row['equipo_id'] is not None}
    equipos_map = {
        equipo.id: equipo.descripcion
        for equipo in Equipo.objects.filter(id__in=equipo_ids)
    }

    data = []
    for row in fuel_data:
        fecha = row['fecha']
        equipo_id_actual = row['equipo_id']
        litros = float(row['total_litros'] or 0)
        horas = horas_por_dia_equipo.get((fecha, equipo_id_actual), 0)
        consumo_por_hora = litros / horas if horas > 0 else 0

        data.append({
            'fecha': fecha.isoformat() if fecha else None,
            'equipo': equipos_map.get(equipo_id_actual, f'Equipo {equipo_id_actual}'),
            'equipo_id': equipo_id_actual,
            'horas_trabajadas': round(horas, 2),
            'consumo': round(litros, 2),
            'consumo_por_hora': round(consumo_por_hora, 2)
        })

    return JsonResponse({'data': data})


def generar_informe_html(filters):
    """
    Genera el informe HTML completo con los datos de producción y combustible.
    """
    fecha_desde = filters.get('fecha_desde', '')
    fecha_hasta = filters.get('fecha_hasta', '')
    unidad_negocio_id = filters.get('unidad_negocio_id', '')
    tipo_operacion_id = filters.get('tipo_operacion_id', '')
    equipo_id = filters.get('equipo_id', '')
    empleado_id = filters.get('empleado_id', '')

    # Obtener nombre de filtros para el encabezado
    unidad_nombre = "Todas"
    if unidad_negocio_id:
        try:
            unidad = UnidadNegocio.objects.get(id=unidad_negocio_id)
            unidad_nombre = unidad.descripcion
        except UnidadNegocio.DoesNotExist:
            pass

    operador_nombre = "Todos"
    if empleado_id:
        try:
            empleado = Empleado.objects.get(id=empleado_id)
            operador_nombre = f"{empleado.nombre} {empleado.apellido}"
        except Empleado.DoesNotExist:
            pass

    equipo_nombre = "Todos"
    if equipo_id:
        try:
            equipo = Equipo.objects.get(id=equipo_id)
            equipo_nombre = f"{equipo.descripcion} ({equipo.patente})" if equipo.patente else equipo.descripcion
        except Equipo.DoesNotExist:
            pass

    tipo_op_nombre = "Todos"
    if tipo_operacion_id:
        try:
            tipo_op = TipoOperacion.objects.get(id=tipo_operacion_id)
            tipo_op_nombre = tipo_op.descripcion
        except TipoOperacion.DoesNotExist:
            pass

    # ========== OBTENER DATOS DE PRODUCCIÓN ==========
    qs_produccion = TableroProduccion.objects.all()
    if fecha_desde:
        qs_produccion = qs_produccion.filter(fecha__gte=fecha_desde)
    if fecha_hasta:
        qs_produccion = qs_produccion.filter(fecha__lte=fecha_hasta)
    if unidad_negocio_id:
        qs_produccion = qs_produccion.filter(unidad_negocio_id=unidad_negocio_id)
    if tipo_operacion_id:
        qs_produccion = qs_produccion.filter(tipo_operacion_id=tipo_operacion_id)
    if equipo_id:
        qs_produccion = qs_produccion.filter(equipo_id=equipo_id)
    if empleado_id:
        qs_produccion = qs_produccion.filter(empleado_id=empleado_id)

    # KPIs de producción
    total_horas = sum(float((p.hr_fin or 0) - (p.hr_inicio or 0)) for p in qs_produccion)
    total_produccion = sum(float(p.produccion or 0) for p in qs_produccion)
    avg_prod_hora = round(total_produccion / total_horas, 2) if total_horas > 0 else 0
    dias_activos = qs_produccion.values('fecha').distinct().count()
    entradas = qs_produccion.count()

    # Obtener equipos para el detalle
    equipo_ids = list(qs_produccion.values_list('equipo_id', flat=True).distinct())
    equipos_map = {e.id: e.descripcion for e in Equipo.objects.filter(id__in=equipo_ids)}

    # Detalle de producción (máximo 100 registros para el email)
    detalle_produccion = []
    for item in qs_produccion.select_related('unidad_negocio', 'tipo_operacion', 'unidad_produccion').order_by('-fecha')[:100]:
        horas_item = float((item.hr_fin or 0) - (item.hr_inicio or 0))
        detalle_produccion.append({
            'fecha': item.fecha.strftime('%Y-%m-%d') if item.fecha else '',
            'equipo': equipos_map.get(item.equipo_id, f'Equipo {item.equipo_id}'),
            'tipo_operacion': item.tipo_operacion.descripcion if item.tipo_operacion else '',
            'unidad_negocio': item.unidad_negocio.descripcion if item.unidad_negocio else '',
            'horas': round(horas_item, 2),
            'produccion': float(item.produccion or 0),
            'unidad_produccion': item.unidad_produccion.descripcion if item.unidad_produccion else '',
        })

    # ========== OBTENER DATOS DE COMBUSTIBLE ==========
    qs_combustible = MovimientoCombustible.objects.all()
    if fecha_desde:
        qs_combustible = qs_combustible.filter(fecha__gte=fecha_desde)
    if fecha_hasta:
        qs_combustible = qs_combustible.filter(fecha__lte=fecha_hasta)
    if unidad_negocio_id:
        qs_combustible = qs_combustible.filter(unidad_negocio_id=unidad_negocio_id)
    if equipo_id:
        qs_combustible = qs_combustible.filter(equipo_id=equipo_id)

    # KPIs de combustible
    total_combustible = sum(float(c.egreso or 0) for c in qs_combustible)
    # Usar las horas de producción (`total_horas`) para calcular consumo por hora
    consumo_por_hora = round(total_combustible / total_horas, 2) if total_horas > 0 else 0

    # Detalle de combustible (máximo 100 registros para el email)
    detalle_combustible = []
    for item in qs_combustible.select_related('equipo', 'tipo_combustible', 'unidad_negocio').order_by('-fecha')[:100]:
        detalle_combustible.append({
            'fecha': item.fecha.strftime('%Y-%m-%d') if item.fecha else '',
            'equipo': item.equipo.descripcion if item.equipo else '',
            'tipo_combustible': item.tipo_combustible.descripcion if item.tipo_combustible else '',
            'unidad_negocio': item.unidad_negocio.descripcion if item.unidad_negocio else '',
            'litros': float(item.egreso or 0),
            'km_hora': float(item.km_hora or 0),
            'precio_litro': float(item.precio_litro or 0),
            'remito': item.remito or '',
        })

    # ========== PREPARAR DATOS PARA GRÁFICOS (ApexCharts en JS) ==========
    from collections import defaultdict
    import json

    fechas_horas = defaultdict(float)
    fechas_produccion = defaultdict(float)
    fechas_combustible = defaultdict(float)

    for p in qs_produccion:
        if p.fecha:
            key = p.fecha.strftime('%Y-%m-%d')
            horas_val = float((p.hr_fin or 0) - (p.hr_inicio or 0))
            fechas_horas[key] += horas_val
            fechas_produccion[key] += float(p.produccion or 0)

    for c in qs_combustible:
        if c.fecha:
            key = c.fecha.strftime('%Y-%m-%d')
            fechas_combustible[key] += float(c.egreso or 0)

    # Listas ordenadas
    keys_h = sorted(fechas_horas.keys())
    vals_h = [round(fechas_horas[k], 2) for k in keys_h]

    keys_p = sorted(fechas_produccion.keys())
    vals_p = [round(fechas_produccion[k], 2) for k in keys_p]

    keys_c = sorted(fechas_combustible.keys())
    vals_c = [round(fechas_combustible[k], 2) for k in keys_c]

    # JSON para insertar en el HTML y usar desde ApexCharts
    js_labels_h = json.dumps(keys_h)
    js_vals_h = json.dumps(vals_h)
    js_labels_p = json.dumps(keys_p)
    js_vals_p = json.dumps(vals_p)
    js_labels_c = json.dumps(keys_c)
    js_vals_c = json.dumps(vals_c)

    # ========== GENERAR HTML ==========
    html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Informe de Producción y Combustible</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            border-bottom: 3px solid #16a34a;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            color: #16a34a;
            margin: 0 0 10px 0;
        }}
        .header p {{
            color: #666;
            margin: 5px 0;
        }}
        .filters-info {{
            background: #f0fdf4;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 30px;
        }}
        .filters-info h3 {{
            margin: 0 0 10px 0;
            color: #16a34a;
        }}
        .filters-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
        }}
        .filter-item {{
            font-size: 14px;
        }}
        .filter-item strong {{
            color: #333;
        }}
        .kpi-section {{
            margin-bottom: 30px;
        }}
        .kpi-section h2 {{
            color: #16a34a;
            border-bottom: 2px solid #16a34a;
            padding-bottom: 10px;
        }}
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        .kpi-card {{
            background: linear-gradient(135deg, #16a34a 0%, #22c55e 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .kpi-card.amber {{
            background: linear-gradient(135deg, #d97706 0%, #f59e0b 100%);
        }}
        .kpi-card .value {{
            font-size: 28px;
            font-weight: bold;
            margin: 10px 0;
        }}
        .kpi-card .label {{
            font-size: 12px;
            opacity: 0.9;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
            font-size: 13px;
        }}
        th {{
            background: #16a34a;
            color: white;
            padding: 12px 8px;
            text-align: left;
            font-weight: 600;
        }}
        th.amber {{
            background: #d97706;
        }}
        td {{
            padding: 10px 8px;
            border-bottom: 1px solid #e5e7eb;
        }}
        tr:hover {{
            background: #f9fafb;
        }}
        tr:nth-child(even) {{
            background: #f3f4f6;
        }}
        .text-right {{
            text-align: right;
        }}
        .footer {{
            margin-top: 30px;
            text-align: center;
            color: #666;
            font-size: 12px;
            border-top: 1px solid #e5e7eb;
            padding-top: 20px;
        }}
        .section-title {{
            color: #16a34a;
            margin: 30px 0 15px 0;
            padding-bottom: 10px;
            border-bottom: 2px solid #e5e7eb;
        }}
        .section-title.amber {{
            color: #d97706;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Informe de Producción y Combustible</h1>
            <p>Generado el {__import__('datetime').datetime.now().strftime('%d/%m/%Y a las %H:%M')}</p>
        </div>

        <div class="filters-info">
            <h3>🔍 Filtros Aplicados</h3>
            <div class="filters-grid">
                <div class="filter-item"><strong>Período:</strong> {fecha_desde or 'Sin límite'} al {fecha_hasta or 'Sin límite'}</div>
                <div class="filter-item"><strong>Unidad de Negocio:</strong> {unidad_nombre}</div>
                <div class="filter-item"><strong>Operador:</strong> {operador_nombre}</div>
                <div class="filter-item"><strong>Equipo:</strong> {equipo_nombre}</div>
                <div class="filter-item"><strong>Tipo Operación:</strong> {tipo_op_nombre}</div>
            </div>
        </div>

        <div class="kpi-section">
            <h2>📈 Resumen de KPIs</h2>
            <div class="kpi-grid">
                <div class="kpi-card">
                    <div class="label">HORAS TOTALES</div>
                    <div class="value">{round(total_horas, 2)}</div>
                </div>
                <div class="kpi-card">
                    <div class="label">PRODUCCIÓN TOTAL</div>
                    <div class="value">{round(total_produccion, 2)}</div>
                </div>
                <div class="kpi-card">
                    <div class="label">PROD / HORA</div>
                    <div class="value">{avg_prod_hora}</div>
                </div>
                <div class="kpi-card">
                    <div class="label">DÍAS / ENTRADAS</div>
                    <div class="value">{dias_activos} / {entradas}</div>
                </div>
                <div class="kpi-card amber">
                    <div class="label">COMBUSTIBLE (L)</div>
                    <div class="value">{round(total_combustible, 2)}</div>
                </div>
                <div class="kpi-card amber">
                    <div class="label">CONSUMO / HORA (L/h)</div>
                    <div class="value">{consumo_por_hora}</div>
                </div>
            </div>
            </div>

            <h2 class="section-title">📊 Gráficos</h2>
            <div id="charts-container" style="margin-bottom:18px;">
                <div id="chart-horas" style="max-width:100%;height:320px;margin-bottom:18px;"></div>
                <div id="chart-produccion" style="max-width:100%;height:320px;margin-bottom:18px;"></div>
                <div id="chart-combustible" style="max-width:100%;height:320px;margin-bottom:18px;"></div>
            </div>
            <script src="https://cdn.jsdelivr.net/npm/apexcharts"></script>
            <script>
            (function(){{
                try{{
                    const labelsHoras = {js_labels_h};
                    const dataHoras = {js_vals_h};
                    const labelsProd = {js_labels_p};
                    const dataProd = {js_vals_p};
                    const labelsComb = {js_labels_c};
                    const dataComb = {js_vals_c};

                    const optionsHoras = {{
                        chart: {{ type: 'line', height: 320, toolbar: {{ show: true }} }},
                        series: [{{ name: 'Horas Trabajadas', data: dataHoras }}],
                        xaxis: {{ categories: labelsHoras }},
                        colors: ['#16a34a']
                    }};
                    new ApexCharts(document.querySelector('#chart-horas'), optionsHoras).render();

                    const optionsProd = {{
                        chart: {{ type: 'bar', height: 320, toolbar: {{ show: true }} }},
                        series: [{{ name: 'Producción', data: dataProd }}],
                        xaxis: {{ categories: labelsProd }},
                        colors: ['#22c55e']
                    }};
                    new ApexCharts(document.querySelector('#chart-produccion'), optionsProd).render();

                    const optionsComb = {{
                        chart: {{ type: 'area', height: 320, toolbar: {{ show: true }} }},
                        series: [{{ name: 'Consumo (L)', data: dataComb }}],
                        xaxis: {{ categories: labelsComb }},
                        colors: ['#f59e0b']
                    }};
                    new ApexCharts(document.querySelector('#chart-combustible'), optionsComb).render();
                }}catch(e){{
                    console.error('Error rendering charts in attached HTML', e);
                }}
            }})();
            </script>

            <h2 class="section-title">📋 Detalle de Producción</h2>
        <table>
            <thead>
                <tr>
                    <th>Fecha</th>
                    <th>Equipo</th>
                    <th>Tipo Operación</th>
                    <th>Unidad Negocio</th>
                    <th class="text-right">Horas</th>
                    <th class="text-right">Producción</th>
                    <th>Unidad Prod.</th>
                </tr>
            </thead>
            <tbody>
"""

    for item in detalle_produccion:
        html += f"""
                <tr>
                    <td>{item['fecha']}</td>
                    <td>{item['equipo']}</td>
                    <td>{item['tipo_operacion']}</td>
                    <td>{item['unidad_negocio']}</td>
                    <td class="text-right">{item['horas']}</td>
                    <td class="text-right">{item['produccion']}</td>
                    <td>{item['unidad_produccion']}</td>
                </tr>
"""

    if not detalle_produccion:
        html += """
                <tr>
                    <td colspan="7" style="text-align: center; color: #666; padding: 20px;">No hay datos de producción</td>
                </tr>
"""

    html += f"""
            </tbody>
        </table>

        <h2 class="section-title amber">⛽ Detalle de Combustible</h2>
        <table>
            <thead>
                <tr>
                    <th class="amber">Fecha</th>
                    <th class="amber">Equipo</th>
                    <th class="amber">Tipo</th>
                    <th class="amber">Unidad Negocio</th>
                    <th class="amber text-right">Litros</th>
                    <th class="amber text-right">Km/Hora</th>
                    <th class="amber text-right">Precio/L</th>
                    <th class="amber">Remito</th>
                </tr>
            </thead>
            <tbody>
"""

    for item in detalle_combustible:
        html += f"""
                <tr>
                    <td>{item['fecha']}</td>
                    <td>{item['equipo']}</td>
                    <td>{item['tipo_combustible']}</td>
                    <td>{item['unidad_negocio']}</td>
                    <td class="text-right">{item['litros']}</td>
                    <td class="text-right">{item['km_hora']}</td>
                    <td class="text-right">{item['precio_litro']}</td>
                    <td>{item['remito']}</td>
                </tr>
"""

    if not detalle_combustible:
        html += """
                <tr>
                    <td colspan="8" style="text-align: center; color: #666; padding: 20px;">No hay datos de combustible</td>
                </tr>
"""

    html += """
            </tbody>
        </table>

        <div class="footer">
            <p>Este informe fue generado automáticamente por el Sistema de Gestión de Producción</p>
            <p>© 2025 - Todos los derechos reservados</p>
        </div>
    </div>
</body>
</html>
"""
    return html


def enviar_informe_email_thread(email_destino, filters, usuario):
    """
    Función que se ejecuta en un thread para generar y enviar el informe por email.
    """
    import traceback
    print(f"[EMAIL] Iniciando generación de informe para {email_destino}")
    try:
        # Generar el HTML del informe
        print(f"[EMAIL] Generando HTML del informe...")
        html_content = generar_informe_html(filters)
        print(f"[EMAIL] HTML generado correctamente ({len(html_content)} bytes)")
        
        # Crear el email
        fecha_desde = filters.get('fecha_desde', 'inicio')
        fecha_hasta = filters.get('fecha_hasta', 'actual')
        
        subject = f'Informe de Producción y Combustible - {fecha_desde} al {fecha_hasta}'
        
        body = f"""
Estimado/a,

Se adjunta el informe de Producción y Combustible solicitado.

Período: {fecha_desde} al {fecha_hasta}
Solicitado por: {usuario}

Este es un mensaje automático, por favor no responda a este correo.

Saludos cordiales,
Sistema de Gestión de Producción
"""
        
        print(f"[EMAIL] Creando mensaje para {email_destino}...")
        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@sistema.com',
            to=[email_destino],
        )
        
        # Adjuntar el HTML como archivo
        email.attach('informe_produccion_combustible.html', html_content, 'text/html')
        
        # Enviar el email
        print(f"[EMAIL] Enviando email...")
        result = email.send(fail_silently=False)
        
        print(f"[EMAIL] ✓ Email enviado exitosamente a {email_destino} (resultado: {result})")
        
    except Exception as e:
        print(f"[EMAIL] ✗ Error enviando email a {email_destino}: {str(e)}")
        print(f"[EMAIL] Traceback completo:")
        traceback.print_exc()


@login_required
def api_enviar_informe_email(request):
    """
    Endpoint para enviar el informe por email.
    Recibe el email y los filtros, genera el informe en un thread y lo envía.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
    
    try:
        data = json.loads(request.body)
        email_destino = data.get('email', '').strip()
        filters = data.get('filters', {})
        
        if not email_destino:
            return JsonResponse({'success': False, 'error': 'El email es requerido'}, status=400)
        
        # Validar formato de email básico
        import re
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email_destino):
            return JsonResponse({'success': False, 'error': 'El formato del email no es válido'}, status=400)
        
        # Obtener nombre de usuario
        usuario = request.user.get_full_name() or request.user.username
        
        # Iniciar el thread para enviar el email
        thread = threading.Thread(
            target=enviar_informe_email_thread,
            args=(email_destino, filters, usuario)
        )
        thread.daemon = True
        thread.start()
        
        return JsonResponse({
            'success': True,
            'message': f'El informe se está generando y será enviado a {email_destino}'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ========== INFORME DE CONSUMO DE COMBUSTIBLE POR EQUIPO ==========

def analizar_consumo_combustible_por_equipo(fecha_desde=None, fecha_hasta=None):
    """
    Analiza el consumo de combustible por equipo para un período específico.
    Calcula el promedio de litros/hora de los últimos 6 meses y detecta consumos elevados.
    
    NOTAS IMPORTANTES:
    - Los tanques están excluidos del análisis
    - Solo se usan COMBUSTIBLES (GasOil, Nafta, Diesel) para los cálculos
    - Se excluyen aceites hidráulicos, lubricantes y otros aceites del análisis de eficiencia
    - Los aceites se incluyen en el detalle de cargas solo como referencia
    
    Retorna un diccionario con:
    - equipos: lista de equipos con datos de consumo (excluyendo tanques)
      * consumo_mes: litros de combustible del período (sin aceites)
      * horas_km: horas/km trabajados
      * consumo_por_hora_km: eficiencia en L/hr del mes actual
      * promedio_ltrs_hora_6_meses: promedio L/hr de los últimos 6 meses
      * es_elevado: True si L/hr actual > 120% del promedio L/hr
    - alertas: lista de equipos con consumo/hora elevado
    - detalle_cargas: todas las cargas (combustibles + aceites) con indicador
    - totales: totales generales
    """
    from datetime import datetime, timedelta
    from django.db.models import Sum, Avg, Count
    from dateutil.relativedelta import relativedelta
    
    # Si no se proporciona rango, usar el mes actual
    if not fecha_hasta:
        fecha_hasta = datetime.now().date()
    if not fecha_desde:
        fecha_desde = fecha_hasta.replace(day=1)
    
    # Calcular fecha de inicio para promedio 6 meses (6 meses antes del mes actual)
    fecha_inicio_6_meses = fecha_desde - relativedelta(months=6)
    
    # Obtener todos los equipos activos (excluyendo tanques)
    equipos = Equipo.objects.filter(activo=True).select_related('tipo_movil').exclude(
        tipo_movil__descripcion__icontains='tanque'
    )
    
    datos_equipos = []
    alertas = []
    
    for equipo in equipos:
        # Consumo del período actual (mes) - Solo combustibles (GasOil, Nafta, Diesel)
        # Excluye aceites hidráulicos, lubricantes, etc.
        consumo_mes = MovimientoCombustible.objects.filter(
            equipo=equipo,
            fecha__gte=fecha_desde,
            fecha__lte=fecha_hasta
        ).filter(
            tipo_combustible__descripcion__iregex=r'(gasoil|gas.?oil|nafta|diesel)'
        ).exclude(
            tipo_combustible__descripcion__icontains='aceite'
        ).aggregate(total=Sum('egreso'))['total'] or 0
        
        # Obtener horas/km del período actual desde TableroProduccion
        produccion_mes = TableroProduccion.objects.filter(
            equipo_id=equipo.id,
            fecha__gte=fecha_desde,
            fecha__lte=fecha_hasta
        )
        
        # Calcular horas totales
        horas_km = 0
        for prod in produccion_mes:
            horas_km += float((prod.hr_fin or 0) - (prod.hr_inicio or 0))
        
        # Consumo por hora/km del mes actual
        consumo_por_hora_km = round(float(consumo_mes) / horas_km, 2) if horas_km > 0 else 0
        
        # Calcular promedio de litros/hora de los últimos 6 meses
        consumos_por_hora_6_meses = []
        for i in range(6):
            mes_inicio = fecha_desde - relativedelta(months=i+1)
            mes_fin = mes_inicio.replace(day=1) + relativedelta(months=1) - timedelta(days=1)
            
            # Consumo del mes histórico - Solo combustibles
            consumo_mes_historico = MovimientoCombustible.objects.filter(
                equipo=equipo,
                fecha__gte=mes_inicio,
                fecha__lte=mes_fin
            ).filter(
                tipo_combustible__descripcion__iregex=r'(gasoil|gas.?oil|nafta|diesel)'
            ).exclude(
                tipo_combustible__descripcion__icontains='aceite'
            ).aggregate(total=Sum('egreso'))['total'] or 0
            
            # Horas del mes histórico
            produccion_mes_historico = TableroProduccion.objects.filter(
                equipo_id=equipo.id,
                fecha__gte=mes_inicio,
                fecha__lte=mes_fin
            )
            
            horas_mes_historico = 0
            for prod in produccion_mes_historico:
                horas_mes_historico += float((prod.hr_fin or 0) - (prod.hr_inicio or 0))
            
            # Calcular litros/hora de ese mes (solo si tuvo horas)
            if horas_mes_historico > 0:
                consumo_por_hora_mes = float(consumo_mes_historico) / horas_mes_historico
                consumos_por_hora_6_meses.append(consumo_por_hora_mes)
        
        # Promedio de litros/hora de los últimos 6 meses
        promedio_ltrs_hora_6_meses = round(sum(consumos_por_hora_6_meses) / len(consumos_por_hora_6_meses), 2) if consumos_por_hora_6_meses else 0
        
        # Detectar consumos elevados (más del 20% sobre el promedio de litros/hora)
        es_elevado = False
        porcentaje_diferencia = 0
        if promedio_ltrs_hora_6_meses > 0 and consumo_por_hora_km > 0:
            porcentaje_diferencia = round(((consumo_por_hora_km - promedio_ltrs_hora_6_meses) / promedio_ltrs_hora_6_meses) * 100, 1)
            if porcentaje_diferencia > 20:
                es_elevado = True
                alertas.append({
                    'equipo': equipo.descripcion,
                    'patente': equipo.patente or 'N/A',
                    'consumo_por_hora_actual': consumo_por_hora_km,
                    'promedio_ltrs_hora': promedio_ltrs_hora_6_meses,
                    'diferencia_porcentual': porcentaje_diferencia
                })
        
        # Solo agregar equipos con consumo en el período
        if float(consumo_mes) > 0:
            datos_equipos.append({
                'id': equipo.id,
                'nombre': equipo.descripcion,
                'patente': equipo.patente or 'N/A',
                'consumo_mes': round(float(consumo_mes), 2),
                'horas_km': round(horas_km, 2),
                'consumo_por_hora_km': consumo_por_hora_km,
                'promedio_ltrs_hora_6_meses': promedio_ltrs_hora_6_meses,
                'es_elevado': es_elevado,
                'diferencia_porcentual': porcentaje_diferencia
            })
    
    # Ordenar por consumo descendente
    datos_equipos.sort(key=lambda x: x['consumo_mes'], reverse=True)
    alertas.sort(key=lambda x: x['diferencia_porcentual'], reverse=True)
    
    # Calcular totales
    total_consumo = sum(e['consumo_mes'] for e in datos_equipos)
    total_horas_km = sum(e['horas_km'] for e in datos_equipos)
    
    # Obtener detalle de cargas de combustible del período (excluyendo tanques)
    equipos_ids = [e['id'] for e in datos_equipos]
    movimientos = MovimientoCombustible.objects.filter(
        equipo_id__in=equipos_ids,
        fecha__gte=fecha_desde,
        fecha__lte=fecha_hasta
    ).select_related('equipo', 'tipo_combustible', 'unidad_negocio').order_by('-fecha', 'equipo__descripcion')
    
    detalle_cargas = []
    for mov in movimientos:
        if mov.egreso > 0:  # Solo cargas (egresos)
            tipo_comb_desc = mov.tipo_combustible.descripcion if mov.tipo_combustible else 'N/A'
            # Determinar si es combustible (usado en cálculos) o aceite/lubricante
            import re
            es_combustible = bool(re.search(r'(gasoil|gas.?oil|nafta|diesel)', tipo_comb_desc, re.IGNORECASE)) and 'aceite' not in tipo_comb_desc.lower()
            
            detalle_cargas.append({
                'fecha': mov.fecha.strftime('%d/%m/%Y'),
                'equipo_id': mov.equipo.id,
                'equipo': mov.equipo.descripcion,
                'patente': mov.equipo.patente or 'N/A',
                'tipo_combustible': tipo_comb_desc,
                'es_combustible': es_combustible,
                'litros': round(float(mov.egreso), 2),
                'km_hora': round(float(mov.km_hora), 2) if mov.km_hora else 0,
                'precio_litro': round(float(mov.precio_litro), 2) if mov.precio_litro else 0,
                'costo_total': round(float(mov.egreso) * float(mov.precio_litro), 2) if mov.precio_litro else 0,
                'unidad_negocio': mov.unidad_negocio.descripcion if mov.unidad_negocio else 'N/A',
                'observaciones': mov.observaciones or ''
            })
    
    return {
        'periodo': {
            'desde': fecha_desde.strftime('%d/%m/%Y'),
            'hasta': fecha_hasta.strftime('%d/%m/%Y')
        },
        'equipos': datos_equipos,
        'alertas': alertas,
        'detalle_cargas': detalle_cargas,
        'totales': {
            'consumo_total': round(total_consumo, 2),
            'horas_km_total': round(total_horas_km, 2),
            'equipos_activos': len(datos_equipos),
            'equipos_con_alerta': len(alertas),
            'total_cargas': len(detalle_cargas)
        }
    }


def generar_html_informe_combustible(datos):
    """
    Genera HTML moderno y minimalista para el informe de consumo de combustible.
    """
    equipos = datos['equipos']
    alertas = datos['alertas']
    totales = datos['totales']
    periodo = datos['periodo']
    detalle_cargas = datos.get('detalle_cargas', [])
    
    # Construir opciones de filtro de equipos (solo equipos con cargas)
    equipos_con_cargas = {}
    for carga in detalle_cargas:
        if carga['equipo_id'] not in equipos_con_cargas:
            equipos_con_cargas[carga['equipo_id']] = carga['equipo']
    
    opciones_equipos = '<option value="">Todos los equipos</option>'
    for equipo_id in sorted(equipos_con_cargas.keys(), key=lambda x: equipos_con_cargas[x]):
        opciones_equipos += f'<option value="{equipo_id}">{equipos_con_cargas[equipo_id]}</option>'
    
    # Construir filas de detalle de cargas
    filas_cargas = ""
    for carga in detalle_cargas:
        clase_tipo = "carga-combustible" if carga['es_combustible'] else "carga-aceite"
        icono_tipo = "⛽" if carga['es_combustible'] else "🛢️"
        
        filas_cargas += f"""
        <tr class="carga-row {clase_tipo}" data-equipo-id="{carga['equipo_id']}">
            <td>{carga['fecha']}</td>
            <td>{carga['equipo']}</td>
            <td>{carga['patente']}</td>
            <td>{icono_tipo} {carga['tipo_combustible']}</td>
            <td class="numero">{carga['litros']:,.2f} L</td>
            <td class="numero">{carga['km_hora']:,.2f}</td>
            <td class="numero">${carga['precio_litro']:,.2f}</td>
            <td class="numero">${carga['costo_total']:,.2f}</td>
            <td class="obs">{carga['observaciones'][:50]}</td>
        </tr>
        """
    
    # Construir tabla de equipos
    filas_equipos = ""
    for eq in equipos:
        clase_alerta = "alerta-row" if eq['es_elevado'] else ""
        icono_alerta = "⚠️ " if eq['es_elevado'] else ""
        
        filas_equipos += f"""
        <tr class="{clase_alerta}">
            <td>{icono_alerta}{eq['nombre']}</td>
            <td>{eq['patente']}</td>
            <td class="numero">{eq['consumo_mes']:,.2f} L</td>
            <td class="numero">{eq['horas_km']:,.2f}</td>
            <td class="numero">{eq['consumo_por_hora_km']:,.2f} L/hr</td>
            <td class="numero">{eq['promedio_ltrs_hora_6_meses']:,.2f} L/hr</td>
        </tr>
        """
    
    # Construir alertas
    alertas_html = ""
    if alertas:
        for alerta in alertas:
            alertas_html += f"""
            <div class="alerta-item">
                <div class="alerta-titulo">⚠️ {alerta['equipo']} ({alerta['patente']})</div>
                <div class="alerta-detalle">
                    Consumo/hora mes actual: <strong>{alerta['consumo_por_hora_actual']:,.2f} L/hr</strong> |
                    Promedio L/hr (últimos 6 meses): <strong>{alerta['promedio_ltrs_hora']:,.2f} L/hr</strong> |
                    Diferencia: <strong class="diferencia-alta">+{alerta['diferencia_porcentual']}%</strong>
                </div>
            </div>
            """
    else:
        alertas_html = '<div class="no-alertas">✓ No se detectaron consumos elevados (equipos con consumo/hora >20% sobre su promedio)</div>'
    
    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Informe de Consumo de Combustible</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                background-color: #f5f5f5;
                padding: 20px;
                color: #333;
            }}
            
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 12px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                overflow: hidden;
            }}
            
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 40px 30px;
                text-align: center;
            }}
            
            .header h1 {{
                font-size: 28px;
                font-weight: 600;
                margin-bottom: 10px;
            }}
            
            .header .periodo {{
                font-size: 16px;
                opacity: 0.9;
            }}
            
            .kpis {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                padding: 30px;
                background: #f8f9fa;
                border-bottom: 1px solid #e0e0e0;
            }}
            
            .kpi-card {{
                background: white;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }}
            
            .kpi-label {{
                font-size: 13px;
                color: #666;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-bottom: 8px;
            }}
            
            .kpi-value {{
                font-size: 28px;
                font-weight: 700;
                color: #667eea;
            }}
            
            .kpi-unit {{
                font-size: 14px;
                color: #999;
                margin-left: 4px;
            }}
            
            .section {{
                padding: 30px;
            }}
            
            .section-title {{
                font-size: 20px;
                font-weight: 600;
                margin-bottom: 20px;
                color: #333;
                border-left: 4px solid #667eea;
                padding-left: 12px;
            }}
            
            .alertas-container {{
                background: #fff3cd;
                border: 1px solid #ffc107;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 30px;
            }}
            
            .alerta-item {{
                padding: 12px;
                margin-bottom: 10px;
                background: white;
                border-radius: 6px;
                border-left: 3px solid #ff9800;
            }}
            
            .alerta-item:last-child {{
                margin-bottom: 0;
            }}
            
            .alerta-titulo {{
                font-weight: 600;
                margin-bottom: 6px;
                font-size: 15px;
            }}
            
            .alerta-detalle {{
                font-size: 13px;
                color: #666;
            }}
            
            .diferencia-alta {{
                color: #d32f2f;
            }}
            
            .no-alertas {{
                text-align: center;
                color: #2e7d32;
                font-weight: 500;
                padding: 10px;
            }}
            
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }}
            
            thead {{
                background: #f8f9fa;
            }}
            
            th {{
                padding: 12px;
                text-align: left;
                font-size: 13px;
                font-weight: 600;
                color: #666;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                border-bottom: 2px solid #e0e0e0;
            }}
            
            td {{
                padding: 12px;
                border-bottom: 1px solid #f0f0f0;
                font-size: 14px;
            }}
            
            td.numero {{
                text-align: right;
                font-variant-numeric: tabular-nums;
            }}
            
            .alerta-row {{
                background: #fff8f0;
            }}
            
            .alerta-row td {{
                border-left: 3px solid #ff9800;
            }}
            
            tr:hover {{
                background: #f8f9fa;
            }}
            
            .filtro-container {{
                margin: 20px 0;
                padding: 15px;
                background: #f8f9fa;
                border-radius: 8px;
                display: flex;
                align-items: center;
                gap: 10px;
            }}
            
            .filtro-label {{
                font-weight: 600;
                color: #666;
                font-size: 14px;
            }}
            
            .filtro-select {{
                padding: 8px 12px;
                border: 1px solid #ddd;
                border-radius: 6px;
                font-size: 14px;
                min-width: 250px;
                cursor: pointer;
                background: white;
            }}
            
            .filtro-select:focus {{
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }}
            
            .obs {{
                max-width: 200px;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
                font-size: 13px;
                color: #999;
            }}
            
            .carga-row td {{
                font-size: 13px;
            }}
            
            .carga-combustible {{
                background: #f1f8f4;
            }}
            
            .carga-combustible:hover {{
                background: #e8f5e9 !important;
            }}
            
            .carga-aceite {{
                background: #f5f5f5;
            }}
            
            .carga-aceite:hover {{
                background: #eeeeee !important;
            }}
            
            .carga-aceite td {{
                color: #757575;
            }}
            
            .hidden {{
                display: none;
            }}
            
            .footer {{
                background: #f8f9fa;
                padding: 20px 30px;
                text-align: center;
                color: #666;
                font-size: 13px;
                border-top: 1px solid #e0e0e0;
            }}
            
            .footer-note {{
                margin-top: 10px;
                font-size: 12px;
                color: #999;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📊 Informe de Consumo de Combustible por Equipo</h1>
                <div class="periodo">Período: {periodo['desde']} - {periodo['hasta']}</div>
            </div>
            
            <div class="kpis">
                <div class="kpi-card">
                    <div class="kpi-label">Consumo Total</div>
                    <div class="kpi-value">{totales['consumo_total']:,.1f}<span class="kpi-unit">L</span></div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label">Horas/Km Totales</div>
                    <div class="kpi-value">{totales['horas_km_total']:,.1f}<span class="kpi-unit">hrs</span></div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label">Equipos Activos</div>
                    <div class="kpi-value">{totales['equipos_activos']}</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label">Equipos con Alerta</div>
                    <div class="kpi-value" style="color: #ff9800;">{totales['equipos_con_alerta']}</div>
                </div>
            </div>
            
            <div class="section">
                <div class="section-title">🚨 Alertas de Consumo Elevado</div>
                <div class="alertas-container">
                    {alertas_html}
                </div>
                
                <div class="section-title">📋 Detalle por Equipo</div>
                <table>
                    <thead>
                        <tr>
                            <th>Equipo</th>
                            <th>Patente</th>
                            <th style="text-align: right;">Consumo Mes Actual</th>
                            <th style="text-align: right;">Horas/Km</th>
                            <th style="text-align: right;">Consumo/Hr</th>
                            <th style="text-align: right;">Prom. L/hr 6M</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filas_equipos}
                    </tbody>
                </table>
                
                <div class="section-title">⛽ Detalle de Cargas de Combustible ({totales.get('total_cargas', 0)} cargas)</div>
                <div class="filtro-container">
                    <span class="filtro-label">🔍 Filtrar por equipo:</span>
                    <select id="filtroEquipo" class="filtro-select" onchange="filtrarCargas()">
                        {opciones_equipos}
                    </select>
                </div>
                <div style="margin: 10px 0; padding: 10px; background: #e3f2fd; border-radius: 6px; font-size: 13px; color: #1565c0;">
                    <strong>ℹ️ Nota:</strong> Los cálculos de consumo (L/hr y promedios) utilizan únicamente <strong>combustibles</strong> (GasOil, Nafta, Diesel). 
                    Los aceites hidráulicos y lubricantes se muestran para referencia pero no se incluyen en el análisis de eficiencia.<br>
                    <span style="display: inline-block; width: 15px; height: 15px; background: #f1f8f4; border: 1px solid #ddd; margin: 5px 5px 0 0; vertical-align: middle;"></span> Combustible (usado en cálculos) &nbsp;&nbsp;
                    <span style="display: inline-block; width: 15px; height: 15px; background: #f5f5f5; border: 1px solid #ddd; margin: 5px 5px 0 0; vertical-align: middle;"></span> Aceite/Lubricante (solo referencia)
                </div>
                <table id="tablaCargas">
                    <thead>
                        <tr>
                            <th>Fecha</th>
                            <th>Equipo</th>
                            <th>Patente</th>
                            <th>Tipo Comb.</th>
                            <th style="text-align: right;">Litros</th>
                            <th style="text-align: right;">Km/Hr</th>
                            <th style="text-align: right;">Precio/L</th>
                            <th style="text-align: right;">Costo Total</th>
                            <th>Observaciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filas_cargas}
                    </tbody>
                </table>
            </div>
            
            <script>
                function filtrarCargas() {{
                    const filtro = document.getElementById('filtroEquipo').value;
                    const filas = document.querySelectorAll('.carga-row');
                    
                    filas.forEach(fila => {{
                        if (filtro === '' || fila.dataset.equipoId === filtro) {{
                            fila.classList.remove('hidden');
                        }} else {{
                            fila.classList.add('hidden');
                        }}
                    }});
                }}
            </script>
            
            <div class="footer">
                <div>Informe generado automáticamente por el Sistema de Gestión de Combustible</div>
                <div class="footer-note">
                    Criterio de alerta: Consumo por hora del mes actual superior al 20% del promedio L/hr de los últimos 6 meses.<br>
                    Los cálculos utilizan únicamente combustibles (GasOil, Nafta, Diesel). Aceites y lubricantes se muestran solo como referencia.
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html


def generar_excel_informe_combustible(datos):
    """
    Genera un archivo Excel con los datos del informe de consumo de combustible.
    Retorna el objeto BytesIO con el archivo.
    """
    from io import BytesIO
    
    wb = Workbook()
    
    # Hoja 1: Resumen
    ws_resumen = wb.active
    ws_resumen.title = "Resumen"
    
    # Título
    ws_resumen['A1'] = 'INFORME DE CONSUMO DE COMBUSTIBLE POR EQUIPO'
    ws_resumen['A1'].font = Font(size=16, bold=True, color="FFFFFF")
    ws_resumen['A1'].fill = PatternFill(start_color="667EEA", end_color="667EEA", fill_type="solid")
    ws_resumen['A1'].alignment = Alignment(horizontal='center')
    ws_resumen.merge_cells('A1:F1')
    
    # Período
    ws_resumen['A3'] = f"Período: {datos['periodo']['desde']} - {datos['periodo']['hasta']}"
    ws_resumen['A3'].font = Font(bold=True)
    
    # KPIs
    ws_resumen['A5'] = 'INDICADORES GENERALES'
    ws_resumen['A5'].font = Font(bold=True, size=12)
    
    kpis_data = [
        ['Consumo Total', f"{datos['totales']['consumo_total']:,.2f} L"],
        ['Horas/Km Totales', f"{datos['totales']['horas_km_total']:,.2f}"],
        ['Equipos Activos', datos['totales']['equipos_activos']],
        ['Equipos con Alerta', datos['totales']['equipos_con_alerta']],
    ]
    
    row = 6
    for kpi in kpis_data:
        ws_resumen[f'A{row}'] = kpi[0]
        ws_resumen[f'B{row}'] = kpi[1]
        ws_resumen[f'A{row}'].font = Font(bold=True)
        row += 1
    
    # Hoja 2: Detalle de Equipos
    ws_detalle = wb.create_sheet("Detalle de Equipos")
    
    # Encabezados
    headers = ['Equipo', 'Patente', 'Consumo Mes Actual (L)', 'Horas/Km', 'Consumo/Hr (L/hr)', 'Prom. L/hr 6M', 'Diferencia %']
    for col_num, header in enumerate(headers, 1):
        cell = ws_detalle.cell(row=1, column=col_num)
        cell.value = header
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="667EEA", end_color="667EEA", fill_type="solid")
        cell.alignment = Alignment(horizontal='center')
    
    # Datos
    for row_num, equipo in enumerate(datos['equipos'], 2):
        ws_detalle.cell(row=row_num, column=1, value=equipo['nombre'])
        ws_detalle.cell(row=row_num, column=2, value=equipo['patente'])
        ws_detalle.cell(row=row_num, column=3, value=equipo['consumo_mes'])
        ws_detalle.cell(row=row_num, column=4, value=equipo['horas_km'])
        ws_detalle.cell(row=row_num, column=5, value=equipo['consumo_por_hora_km'])
        ws_detalle.cell(row=row_num, column=6, value=equipo['promedio_ltrs_hora_6_meses'])
        ws_detalle.cell(row=row_num, column=7, value=equipo['diferencia_porcentual'])
        
        # Resaltar filas con alerta
        if equipo['es_elevado']:
            for col in range(1, 8):
                ws_detalle.cell(row=row_num, column=col).fill = PatternFill(
                    start_color="FFF3CD", end_color="FFF3CD", fill_type="solid"
                )
    
    # Ajustar anchos de columna
    for col in range(1, 8):
        ws_detalle.column_dimensions[get_column_letter(col)].width = 18
    
    # Hoja 3: Alertas
    if datos['alertas']:
        ws_alertas = wb.create_sheet("Alertas")
        
        ws_alertas['A1'] = 'EQUIPOS CON CONSUMO ELEVADO'
        ws_alertas['A1'].font = Font(size=14, bold=True, color="FFFFFF")
        ws_alertas['A1'].fill = PatternFill(start_color="FF9800", end_color="FF9800", fill_type="solid")
        ws_alertas.merge_cells('A1:D1')
        
        headers_alertas = ['Equipo', 'Patente', 'Consumo/Hr Actual (L/hr)', 'Prom. L/hr 6M', 'Diferencia %']
        for col_num, header in enumerate(headers_alertas, 1):
            cell = ws_alertas.cell(row=3, column=col_num)
            cell.value = header
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="FFE0B2", end_color="FFE0B2", fill_type="solid")
        
        for row_num, alerta in enumerate(datos['alertas'], 4):
            ws_alertas.cell(row=row_num, column=1, value=alerta['equipo'])
            ws_alertas.cell(row=row_num, column=2, value=alerta['patente'])
            ws_alertas.cell(row=row_num, column=3, value=alerta['consumo_por_hora_actual'])
            ws_alertas.cell(row=row_num, column=4, value=alerta['promedio_ltrs_hora'])
            ws_alertas.cell(row=row_num, column=5, value=f"+{alerta['diferencia_porcentual']}%")
        
        for col in range(1, 6):
            ws_alertas.column_dimensions[get_column_letter(col)].width = 20
    
    # Hoja 4: Detalle de Cargas
    if datos.get('detalle_cargas'):
        ws_cargas = wb.create_sheet("Detalle de Cargas")
        
        ws_cargas['A1'] = 'DETALLE DE CARGAS DE COMBUSTIBLE'
        ws_cargas['A1'].font = Font(size=14, bold=True, color="FFFFFF")
        ws_cargas['A1'].fill = PatternFill(start_color="667EEA", end_color="667EEA", fill_type="solid")
        ws_cargas.merge_cells('A1:J1')
        
        # Nota sobre tipos de combustible
        ws_cargas['A2'] = 'Nota: Solo se usan GasOil, Nafta y Diesel para cálculos de consumo. Aceites/lubricantes son solo referencia.'
        ws_cargas['A2'].font = Font(size=10, italic=True, color="1565C0")
        ws_cargas.merge_cells('A2:J2')
        
        headers_cargas = ['Fecha', 'Equipo', 'Patente', 'Tipo Combustible', 'Categoría', 'Litros', 'Km/Hr', 'Precio/L', 'Costo Total', 'Observaciones']
        for col_num, header in enumerate(headers_cargas, 1):
            cell = ws_cargas.cell(row=3, column=col_num)
            cell.value = header
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="E8EAF6", end_color="E8EAF6", fill_type="solid")
            cell.alignment = Alignment(horizontal='center')
        
        for row_num, carga in enumerate(datos['detalle_cargas'], 4):
            ws_cargas.cell(row=row_num, column=1, value=carga['fecha'])
            ws_cargas.cell(row=row_num, column=2, value=carga['equipo'])
            ws_cargas.cell(row=row_num, column=3, value=carga['patente'])
            ws_cargas.cell(row=row_num, column=4, value=carga['tipo_combustible'])
            ws_cargas.cell(row=row_num, column=5, value='Combustible' if carga['es_combustible'] else 'Aceite/Lubr.')
            ws_cargas.cell(row=row_num, column=6, value=carga['litros'])
            ws_cargas.cell(row=row_num, column=7, value=carga['km_hora'])
            ws_cargas.cell(row=row_num, column=8, value=carga['precio_litro'])
            ws_cargas.cell(row=row_num, column=9, value=carga['costo_total'])
            ws_cargas.cell(row=row_num, column=10, value=carga['observaciones'])
            
            # Formato diferente para combustibles vs aceites
            fill_color = "F1F8F4" if carga['es_combustible'] else "F5F5F5"
            for col in range(1, 11):
                ws_cargas.cell(row=row_num, column=col).fill = PatternFill(
                    start_color=fill_color, end_color=fill_color, fill_type="solid"
                )
        
        # Ajustar anchos de columna
        widths = [12, 25, 12, 18, 15, 12, 10, 12, 15, 30]
        for col_num, width in enumerate(widths, 1):
            ws_cargas.column_dimensions[get_column_letter(col_num)].width = width
    
    # Guardar en BytesIO
    excel_file = BytesIO()
    wb.save(excel_file)
    excel_file.seek(0)
    
    return excel_file


def enviar_informe_combustible_thread(emails_destino, fecha_desde=None, fecha_hasta=None, usuario='Sistema'):
    """
    Función que se ejecuta en un thread para generar y enviar el informe de combustible.
    """
    import traceback
    from datetime import datetime
    
    print(f"[INFORME COMBUSTIBLE] Iniciando generación para {emails_destino}")
    
    try:
        # Analizar datos
        print(f"[INFORME COMBUSTIBLE] Analizando datos...")
        datos = analizar_consumo_combustible_por_equipo(fecha_desde, fecha_hasta)
        
        # Generar HTML
        print(f"[INFORME COMBUSTIBLE] Generando HTML...")
        html_content = generar_html_informe_combustible(datos)
        
        # Generar Excel
        print(f"[INFORME COMBUSTIBLE] Generando Excel...")
        excel_file = generar_excel_informe_combustible(datos)
        
        # Preparar email
        periodo_str = f"{datos['periodo']['desde']} al {datos['periodo']['hasta']}"
        subject = f'Informe de Consumo de Combustible por Equipo - {periodo_str}'
        
        body = f"""
Estimado/a,

Se adjunta el informe de consumo de combustible por equipo para el período {periodo_str}.

RESUMEN:
- Consumo total: {datos['totales']['consumo_total']:,.2f} litros
- Equipos activos: {datos['totales']['equipos_activos']}
- Equipos con consumo elevado: {datos['totales']['equipos_con_alerta']}

Los datos completos se encuentran en el archivo Excel adjunto.
El informe HTML adjunto incluye visualizaciones y alertas detalladas.

Solicitado por: {usuario}
Fecha de generación: {datetime.now().strftime('%d/%m/%Y %H:%M')}

Este es un mensaje automático, por favor no responda a este correo.

Saludos cordiales,
Sistema de Gestión de Combustible
"""
        
        # Crear email
        print(f"[INFORME COMBUSTIBLE] Creando mensaje...")
        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@sistema.com',
            to=emails_destino if isinstance(emails_destino, list) else [emails_destino],
        )
        
        # Adjuntar HTML
        email.attach('informe_combustible.html', html_content, 'text/html')
        
        # Adjuntar Excel
        filename_excel = f"informe_combustible_{datos['periodo']['desde'].replace('/', '-')}_al_{datos['periodo']['hasta'].replace('/', '-')}.xlsx"
        email.attach(filename_excel, excel_file.read(), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        
        # Enviar
        print(f"[INFORME COMBUSTIBLE] Enviando email...")
        result = email.send(fail_silently=False)
        
        print(f"[INFORME COMBUSTIBLE] ✓ Email enviado exitosamente (resultado: {result})")
        
    except Exception as e:
        print(f"[INFORME COMBUSTIBLE] ✗ Error: {str(e)}")
        traceback.print_exc()


@login_required
def api_enviar_informe_combustible(request):
    """
    Endpoint para enviar el informe de consumo de combustible por equipo.
    POST con body JSON:
    {
        "email": "destino@email.com" o ["email1@test.com", "email2@test.com"],
        "fecha_desde": "2024-01-01" (opcional, por defecto inicio del mes actual),
        "fecha_hasta": "2024-01-31" (opcional, por defecto fecha actual)
    }
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
    
    try:
        from datetime import datetime
        
        data = json.loads(request.body)
        email_destino = data.get('email', '').strip()
        fecha_desde_str = data.get('fecha_desde', '')
        fecha_hasta_str = data.get('fecha_hasta', '')
        
        # Validar email(s)
        import re
        emails = []
        if isinstance(email_destino, list):
            emails = email_destino
        elif email_destino:
            emails = [email_destino]
        else:
            return JsonResponse({'success': False, 'error': 'El email es requerido'}, status=400)
        
        for email in emails:
            if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
                return JsonResponse({'success': False, 'error': f'Formato de email inválido: {email}'}, status=400)
        
        # Parsear fechas
        fecha_desde = None
        fecha_hasta = None
        
        if fecha_desde_str:
            try:
                fecha_desde = datetime.strptime(fecha_desde_str, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({'success': False, 'error': 'Formato de fecha_desde inválido (usar YYYY-MM-DD)'}, status=400)
        
        if fecha_hasta_str:
            try:
                fecha_hasta = datetime.strptime(fecha_hasta_str, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({'success': False, 'error': 'Formato de fecha_hasta inválido (usar YYYY-MM-DD)'}, status=400)
        
        # Obtener usuario
        usuario = request.user.get_full_name() or request.user.username
        
        # Iniciar thread para enviar el email
        thread = threading.Thread(
            target=enviar_informe_combustible_thread,
            args=(emails, fecha_desde, fecha_hasta, usuario)
        )
        thread.daemon = True
        thread.start()
        
        return JsonResponse({
            'success': True,
            'message': f'El informe se está generando y será enviado a {", ".join(emails)}'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON inválido'}, status=400)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
