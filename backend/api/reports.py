from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from typing import Dict, Iterable, List, Optional

from django.db.models import ExpressionWrapper, F, FloatField, Sum

from .models import (
    Equipo,
    MovimientoCombustible,
    TableroProduccion,
    TipoOperacion,
    UnidadNegocio,
    UnidadProduccion,
)


@dataclass
class ReportItem:
    unidad_negocio_id: int
    unidad_negocio: str
    equipo_id: int
    equipo: str
    unidad_produccion: str
    produccion: float
    horas: float
    combustible: float
    prod_por_hora: Optional[float] = None
    litros_por_unidad: Optional[float] = None


@dataclass
class UnidadGroup:
    unidad_negocio_id: int
    unidad_negocio: str
    items: List[ReportItem]
    subtotal_produccion: float
    subtotal_horas: float
    subtotal_combustible: float
    subtotal_prod_por_hora: Optional[float] = None
    subtotal_litros_por_unidad: Optional[float] = None


@dataclass
class ResumenSeccion:
    tipo_operacion: str
    unidades: List[UnidadGroup]
    total_produccion: float
    total_horas: float
    total_combustible: float
    total_prod_por_hora: Optional[float] = None
    total_litros_por_unidad: Optional[float] = None


@dataclass
class OtraUnidadItem:
    unidad_negocio_id: int
    unidad_negocio: str
    horas: float
    combustible: float
    consumo_por_hora: float


@dataclass
class OtrasUnidadesResumen:
    items: List[OtraUnidadItem]
    total_horas: float
    total_combustible: float
    total_consumo_por_hora: float


def get_tipo_operacion_id(descripcion: str) -> Optional[int]:
    tipo = TipoOperacion.objects.filter(descripcion__iexact=descripcion).first()
    return tipo.id if tipo else None


def _get_unidad_map(ids: Iterable[int]) -> Dict[int, str]:
    unidades = UnidadNegocio.objects.filter(id__in=list(ids)).values('id', 'descripcion')
    return {u['id']: (u['descripcion'] or f"Unidad {u['id']}") for u in unidades}


def _get_equipo_map(ids: Iterable[int]) -> Dict[int, str]:
    equipos = Equipo.objects.filter(id__in=list(ids)).values('id', 'descripcion')
    return {e['id']: (e['descripcion'] or f"Equipo {e['id']}") for e in equipos}


def _get_unidad_produccion_map(ids: Iterable[int]) -> Dict[int, str]:
    unidades = UnidadProduccion.objects.filter(id__in=list(ids)).values('id', 'descripcion')
    return {u['id']: (u['descripcion'] or f"Unidad {u['id']}") for u in unidades}


def _horas_expr():
    return ExpressionWrapper(F('hr_fin') - F('hr_inicio'), output_field=FloatField())


def build_produccion_resumen(tipo_operacion_desc: str, fecha_desde: date, fecha_hasta: date, incluir_rates: bool) -> ResumenSeccion:
    tipo_id = get_tipo_operacion_id(tipo_operacion_desc)
    if not tipo_id:
        return ResumenSeccion(tipo_operacion_desc, [], 0, 0, 0, None, None)

    qs = TableroProduccion.objects.filter(
        fecha__gte=fecha_desde,
        fecha__lte=fecha_hasta,
        tipo_operacion_id=tipo_id,
    ).annotate(horas_trabajadas=_horas_expr())

    data = list(
        qs.values('unidad_negocio_id', 'equipo_id')
        .annotate(
            total_produccion=Sum('produccion'),
            total_horas=Sum('horas_trabajadas'),
        )
        .order_by('unidad_negocio_id', 'equipo_id')
    )

    if not data:
        return ResumenSeccion(tipo_operacion_desc, [], 0, 0, 0, None, None)

    unidad_ids = {row['unidad_negocio_id'] for row in data}
    equipo_ids = {row['equipo_id'] for row in data}
    unidades_map = _get_unidad_map(unidad_ids)
    equipos_map = _get_equipo_map(equipo_ids)

    fuel_data = (
        MovimientoCombustible.objects.filter(
            fecha__gte=fecha_desde,
            fecha__lte=fecha_hasta,
            unidad_negocio_id__in=list(unidad_ids),
            equipo_id__in=list(equipo_ids),
        )
        .values('unidad_negocio_id', 'equipo_id')
        .annotate(total_litros=Sum('egreso'))
    )
    combustible_map = {
        (row['unidad_negocio_id'], row['equipo_id']): float(row['total_litros'] or 0)
        for row in fuel_data
    }

    unidades_por_equipo: Dict[int, List[int]] = defaultdict(list)
    for row in qs.values('equipo_id', 'unidad_produccion_id').distinct():
        unidades_por_equipo[row['equipo_id']].append(row['unidad_produccion_id'])

    unidad_prod_ids = {u for ulist in unidades_por_equipo.values() for u in ulist}
    unidades_prod_map = _get_unidad_produccion_map(unidad_prod_ids)

    grouped: Dict[int, List[ReportItem]] = defaultdict(list)

    for row in data:
        unidad_id = row['unidad_negocio_id']
        equipo_id = row['equipo_id']
        produccion = float(row['total_produccion'] or 0)
        horas = float(row['total_horas'] or 0)
        litros = float(combustible_map.get((unidad_id, equipo_id), 0))

        unidad_ids_equipo = unidades_por_equipo.get(equipo_id, [])
        if len(set(unidad_ids_equipo)) == 1:
            unidad_prod_id = unidad_ids_equipo[0]
            unidad_label = unidades_prod_map.get(unidad_prod_id, f"Unidad {unidad_prod_id}")
        elif len(set(unidad_ids_equipo)) > 1:
            unidad_label = "Múltiples"
        else:
            unidad_label = "-"

        prod_por_hora = (produccion / horas) if incluir_rates and horas > 0 else None
        litros_por_unidad = (litros / produccion) if incluir_rates and produccion > 0 else None

        grouped[unidad_id].append(
            ReportItem(
                unidad_negocio_id=unidad_id,
                unidad_negocio=unidades_map.get(unidad_id, f"Unidad {unidad_id}"),
                equipo_id=equipo_id,
                equipo=equipos_map.get(equipo_id, f"Equipo {equipo_id}"),
                unidad_produccion=unidad_label,
                produccion=produccion,
                horas=horas,
                combustible=litros,
                prod_por_hora=round(prod_por_hora, 2) if prod_por_hora is not None else None,
                litros_por_unidad=round(litros_por_unidad, 2) if litros_por_unidad is not None else None,
            )
        )

    unidades: List[UnidadGroup] = []
    total_produccion = 0.0
    total_horas = 0.0
    total_combustible = 0.0

    for unidad_id in sorted(grouped.keys()):
        items = sorted(grouped[unidad_id], key=lambda x: (x.equipo, x.unidad_produccion))
        subtotal_produccion = sum(i.produccion for i in items)
        subtotal_horas = sum(i.horas for i in items)
        subtotal_combustible = sum(i.combustible for i in items)

        subtotal_prod_por_hora = None
        subtotal_litros_por_unidad = None
        if incluir_rates:
            subtotal_prod_por_hora = round(subtotal_produccion / subtotal_horas, 2) if subtotal_horas > 0 else 0
            subtotal_litros_por_unidad = round(subtotal_combustible / subtotal_produccion, 2) if subtotal_produccion > 0 else 0

        unidades.append(
            UnidadGroup(
                unidad_negocio_id=unidad_id,
                unidad_negocio=unidades_map.get(unidad_id, f"Unidad {unidad_id}"),
                items=items,
                subtotal_produccion=round(subtotal_produccion, 2),
                subtotal_horas=round(subtotal_horas, 2),
                subtotal_combustible=round(subtotal_combustible, 2),
                subtotal_prod_por_hora=subtotal_prod_por_hora,
                subtotal_litros_por_unidad=subtotal_litros_por_unidad,
            )
        )

        total_produccion += subtotal_produccion
        total_horas += subtotal_horas
        total_combustible += subtotal_combustible

    total_prod_por_hora = None
    total_litros_por_unidad = None
    if incluir_rates:
        total_prod_por_hora = round(total_produccion / total_horas, 2) if total_horas > 0 else 0
        total_litros_por_unidad = round(total_combustible / total_produccion, 2) if total_produccion > 0 else 0

    return ResumenSeccion(
        tipo_operacion_desc,
        unidades,
        round(total_produccion, 2),
        round(total_horas, 2),
        round(total_combustible, 2),
        total_prod_por_hora,
        total_litros_por_unidad,
    )


def build_otras_unidades_resumen(fecha_desde: date, fecha_hasta: date, excluded_tipo_ids: List[int]) -> OtrasUnidadesResumen:
    qs_prod = TableroProduccion.objects.filter(fecha__gte=fecha_desde, fecha__lte=fecha_hasta)
    if excluded_tipo_ids:
        qs_prod = qs_prod.exclude(tipo_operacion_id__in=excluded_tipo_ids)

    qs_prod = qs_prod.annotate(horas_trabajadas=_horas_expr())

    prod_data = (
        qs_prod.values('unidad_negocio_id')
        .annotate(total_horas=Sum('horas_trabajadas'))
        .order_by('unidad_negocio_id')
    )

    unidad_ids = [row['unidad_negocio_id'] for row in prod_data]
    unidades_map = _get_unidad_map(unidad_ids)

    fuel_data = (
        MovimientoCombustible.objects.filter(
            fecha__gte=fecha_desde,
            fecha__lte=fecha_hasta,
            unidad_negocio_id__in=unidad_ids,
        )
        .values('unidad_negocio_id')
        .annotate(total_litros=Sum('egreso'))
    )
    combustible_map = {row['unidad_negocio_id']: float(row['total_litros'] or 0) for row in fuel_data}

    items: List[OtraUnidadItem] = []
    total_horas = 0.0
    total_combustible = 0.0

    for row in prod_data:
        unidad_id = row['unidad_negocio_id']
        horas = float(row['total_horas'] or 0)
        litros = float(combustible_map.get(unidad_id, 0))
        consumo_por_hora = litros / horas if horas > 0 else 0

        items.append(
            OtraUnidadItem(
                unidad_negocio_id=unidad_id,
                unidad_negocio=unidades_map.get(unidad_id, f"Unidad {unidad_id}"),
                horas=round(horas, 2),
                combustible=round(litros, 2),
                consumo_por_hora=round(consumo_por_hora, 2),
            )
        )

        total_horas += horas
        total_combustible += litros

    total_consumo_por_hora = total_combustible / total_horas if total_horas > 0 else 0

    return OtrasUnidadesResumen(
        items=items,
        total_horas=round(total_horas, 2),
        total_combustible=round(total_combustible, 2),
        total_consumo_por_hora=round(total_consumo_por_hora, 2),
    )


def render_html_report(
    fecha_objetivo: date,
    fecha_mes_desde: date,
    fecha_mes_hasta: date,
    proceso_dia: ResumenSeccion,
    proceso_mes: ResumenSeccion,
    carga_dia: ResumenSeccion,
    carga_mes: ResumenSeccion,
    otras_dia: OtrasUnidadesResumen,
    otras_mes: OtrasUnidadesResumen,
) -> str:
    def _render_tabla_produccion(resumen: ResumenSeccion, incluir_rates: bool) -> str:
        headers = (
            "<tr>"
            "<th>Unidad Negocio</th>"
            "<th>Equipo</th>"
            "<th class=\"num\">Producción</th>"
            "<th>Unidad</th>"
            "<th class=\"num\">Horas</th>"
            "<th class=\"num\">Combustible (L)</th>"
        )
        if incluir_rates:
            headers += "<th class=\"num\">Prod/Hora</th><th class=\"num\">L/Unidad Prod</th>"
        headers += "</tr>"

        rows = []
        for unidad in resumen.unidades:
            for item in unidad.items:
                row = (
                    "<tr>"
                    f"<td>{unidad.unidad_negocio}</td>"
                    f"<td>{item.equipo}</td>"
                    f"<td class=\"num\">{item.produccion:.2f}</td>"
                    f"<td>{item.unidad_produccion}</td>"
                    f"<td class=\"num\">{item.horas:.2f}</td>"
                    f"<td class=\"num\">{item.combustible:.2f}</td>"
                )
                if incluir_rates:
                    row += (
                        f"<td class=\"num\">{item.prod_por_hora or 0:.2f}</td>"
                        f"<td class=\"num\">{item.litros_por_unidad or 0:.2f}</td>"
                    )
                row += "</tr>"
                rows.append(row)

            subtotal_row = (
                "<tr class=\"subtotal\">"
                f"<td colspan=\"2\"><strong>Subtotal {unidad.unidad_negocio}</strong></td>"
                f"<td class=\"num\"><strong>{unidad.subtotal_produccion:.2f}</strong></td>"
                "<td></td>"
                f"<td class=\"num\"><strong>{unidad.subtotal_horas:.2f}</strong></td>"
                f"<td class=\"num\"><strong>{unidad.subtotal_combustible:.2f}</strong></td>"
            )
            if incluir_rates:
                subtotal_row += (
                    f"<td class=\"num\"><strong>{(unidad.subtotal_prod_por_hora or 0):.2f}</strong></td>"
                    f"<td class=\"num\"><strong>{(unidad.subtotal_litros_por_unidad or 0):.2f}</strong></td>"
                )
            subtotal_row += "</tr>"
            rows.append(subtotal_row)

        if not rows:
            col_span = 6 + (2 if incluir_rates else 0)
            rows.append(
                f"<tr><td colspan=\"{col_span}\" class=\"empty\">No hay datos para este período.</td></tr>"
            )

        total_cols = 6 + (2 if incluir_rates else 0)
        total_row = (
            "<tr class=\"total\">"
            f"<td colspan=\"2\"><strong>Total General</strong></td>"
            f"<td class=\"num\"><strong>{resumen.total_produccion:.2f}</strong></td>"
            "<td></td>"
            f"<td class=\"num\"><strong>{resumen.total_horas:.2f}</strong></td>"
            f"<td class=\"num\"><strong>{resumen.total_combustible:.2f}</strong></td>"
        )
        if incluir_rates:
            total_row += (
                f"<td class=\"num\"><strong>{(resumen.total_prod_por_hora or 0):.2f}</strong></td>"
                f"<td class=\"num\"><strong>{(resumen.total_litros_por_unidad or 0):.2f}</strong></td>"
            )
        total_row += "</tr>"

        table = (
            "<table class=\"report-table\">"
            f"<thead>{headers}</thead>"
            f"<tbody>{''.join(rows)}{total_row}</tbody>"
            "</table>"
        )
        return table

    def _render_tabla_otras(resumen: OtrasUnidadesResumen) -> str:
        rows = []
        for item in resumen.items:
            rows.append(
                "<tr>"
                f"<td>{item.unidad_negocio}</td>"
                f"<td class=\"num\">{item.horas:.2f}</td>"
                f"<td class=\"num\">{item.combustible:.2f}</td>"
                f"<td class=\"num\">{item.consumo_por_hora:.2f}</td>"
                "</tr>"
            )

        if not rows:
            rows.append("<tr><td colspan=\"4\" class=\"empty\">No hay datos para este período.</td></tr>")

        total_row = (
            "<tr class=\"total\">"
            "<td><strong>Total General</strong></td>"
            f"<td class=\"num\"><strong>{resumen.total_horas:.2f}</strong></td>"
            f"<td class=\"num\"><strong>{resumen.total_combustible:.2f}</strong></td>"
            f"<td class=\"num\"><strong>{resumen.total_consumo_por_hora:.2f}</strong></td>"
            "</tr>"
        )

        table = (
            "<table class=\"report-table\">"
            "<thead>"
            "<tr><th>Unidad Negocio</th><th class=\"num\">Horas</th><th class=\"num\">Combustible (L)</th><th class=\"num\">Consumo (L/h)</th></tr>"
            "</thead>"
            f"<tbody>{''.join(rows)}{total_row}</tbody>"
            "</table>"
        )
        return table

    style = """
    <style>
        body { font-family: Arial, sans-serif; color: #111827; }
        h1, h2 { color: #0f766e; }
        .section { margin: 24px 0; }
        .report-table { width: 100%; border-collapse: collapse; font-size: 13px; }
        .report-table th { background: #0f766e; color: white; text-align: left; padding: 8px; }
        .report-table td { border-bottom: 1px solid #e5e7eb; padding: 8px; }
        .report-table .num { text-align: right; }
        .report-table .subtotal { background: #f1f5f9; font-weight: 600; }
        .report-table .total { background: #e2e8f0; font-weight: 700; }
        .report-table .empty { text-align: center; color: #6b7280; padding: 12px; }
        .meta { background: #f8fafc; padding: 12px; border-radius: 6px; }
    </style>
    """

    html = f"""
    <html>
    <head>{style}</head>
    <body>
        <h1>Informe Diario - Producción y Combustible</h1>
        <div class="meta">
            <p><strong>Fecha objetivo:</strong> {fecha_objetivo.strftime('%d/%m/%Y')}</p>
            <p><strong>Acumulado mes:</strong> {fecha_mes_desde.strftime('%d/%m/%Y')} al {fecha_mes_hasta.strftime('%d/%m/%Y')}</p>
        </div>

        <div class="section">
            <h2>PROCESO - Día</h2>
            {_render_tabla_produccion(proceso_dia, incluir_rates=False)}
        </div>
        <div class="section">
            <h2>PROCESO - Acumulado Mes</h2>
            {_render_tabla_produccion(proceso_mes, incluir_rates=True)}
        </div>

        <div class="section">
            <h2>CARGA - Día</h2>
            {_render_tabla_produccion(carga_dia, incluir_rates=False)}
        </div>
        <div class="section">
            <h2>CARGA - Acumulado Mes</h2>
            {_render_tabla_produccion(carga_mes, incluir_rates=True)}
        </div>

        <div class="section">
            <h2>Otras Unidades de Negocio - Día</h2>
            {_render_tabla_otras(otras_dia)}
        </div>
        <div class="section">
            <h2>Otras Unidades de Negocio - Acumulado Mes</h2>
            {_render_tabla_otras(otras_mes)}
        </div>
    </body>
    </html>
    """
    return html
