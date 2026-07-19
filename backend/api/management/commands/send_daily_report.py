from __future__ import annotations

from datetime import datetime, timedelta

from django.conf import settings
from django.core.mail import EmailMessage
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from api.reports import (
    build_otras_unidades_resumen,
    build_produccion_resumen,
    get_tipo_operacion_id,
    render_html_report,
)


class Command(BaseCommand):
    help = "Envía el informe diario de producción y combustible (día anterior)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--date",
            help="Fecha objetivo en formato YYYY-MM-DD (por defecto: ayer)",
            default=None,
        )
        parser.add_argument(
            "--to",
            help="Email destino (sobrescribe DAILY_REPORT_EMAIL_TO)",
            default=None,
        )

    def handle(self, *args, **options):
        date_str = options.get("date")
        to_override = options.get("to")

        if date_str:
            try:
                target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError as exc:
                raise CommandError("Formato de fecha inválido. Use YYYY-MM-DD.") from exc
        else:
            target_date = timezone.localdate() - timedelta(days=1)

        month_start = target_date.replace(day=1)
        month_end = target_date

        proceso_dia = build_produccion_resumen("PROCESO", target_date, target_date, incluir_rates=False)
        proceso_mes = build_produccion_resumen("PROCESO", month_start, month_end, incluir_rates=True)
        carga_dia = build_produccion_resumen("CARGA", target_date, target_date, incluir_rates=False)
        carga_mes = build_produccion_resumen("CARGA", month_start, month_end, incluir_rates=True)

        excluded_ids = [
            i for i in [
                get_tipo_operacion_id("PROCESO"),
                get_tipo_operacion_id("CARGA"),
            ]
            if i is not None
        ]

        otras_dia = build_otras_unidades_resumen(target_date, target_date, excluded_tipo_ids=excluded_ids)
        otras_mes = build_otras_unidades_resumen(month_start, month_end, excluded_tipo_ids=excluded_ids)

        html = render_html_report(
            target_date,
            month_start,
            month_end,
            proceso_dia,
            proceso_mes,
            carga_dia,
            carga_mes,
            otras_dia,
            otras_mes,
        )

        to_setting = getattr(settings, "DAILY_REPORT_EMAIL_TO", "")
        to_email = to_override or to_setting
        if not to_email:
            raise CommandError("No hay email destino. Configure DAILY_REPORT_EMAIL_TO en .env o use --to.")

        to_list = [email.strip() for email in to_email.split(",") if email.strip()]
        if not to_list:
            raise CommandError("Email destino vacío.")

        subject = f"Informe diario producción y combustible - {target_date.strftime('%d/%m/%Y')}"
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None) or getattr(settings, "EMAIL_HOST_USER", "")
        if not from_email:
            raise CommandError("No hay remitente configurado (DEFAULT_FROM_EMAIL o EMAIL_HOST_USER).")

        email = EmailMessage(subject=subject, body=html, from_email=from_email, to=to_list)
        email.content_subtype = "html"
        email.send(fail_silently=False)

        self.stdout.write(self.style.SUCCESS(f"Informe enviado a {', '.join(to_list)}"))
