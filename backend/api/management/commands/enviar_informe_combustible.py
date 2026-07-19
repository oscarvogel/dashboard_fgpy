"""
Comando Django para enviar automáticamente el informe de consumo de combustible por equipo.

Uso:
    python manage.py enviar_informe_combustible --emails email1@test.com email2@test.com
    python manage.py enviar_informe_combustible --emails email@test.com --fecha-desde 2024-01-01 --fecha-hasta 2024-01-31
    python manage.py enviar_informe_combustible --emails email@test.com --mes-actual

Ejemplos:
    # Enviar informe del mes actual a un email
    python manage.py enviar_informe_combustible --emails admin@empresa.com --mes-actual
    
    # Enviar informe de un período específico a múltiples emails
    python manage.py enviar_informe_combustible --emails email1@test.com email2@test.com --fecha-desde 2024-01-01 --fecha-hasta 2024-01-31
    
    # Enviar informe del mes anterior
    python manage.py enviar_informe_combustible --emails admin@empresa.com --mes-anterior
"""

from django.core.management.base import BaseCommand
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from api.views import enviar_informe_combustible_thread


class Command(BaseCommand):
    help = 'Envía el informe de consumo de combustible por equipo por email'

    def add_arguments(self, parser):
        parser.add_argument(
            '--emails',
            nargs='+',
            type=str,
            required=True,
            help='Email(s) de destino (separados por espacio)'
        )
        
        parser.add_argument(
            '--fecha-desde',
            type=str,
            help='Fecha de inicio del período (formato YYYY-MM-DD)'
        )
        
        parser.add_argument(
            '--fecha-hasta',
            type=str,
            help='Fecha de fin del período (formato YYYY-MM-DD)'
        )
        
        parser.add_argument(
            '--mes-actual',
            action='store_true',
            help='Usar el mes actual (desde el día 1 hasta hoy)'
        )
        
        parser.add_argument(
            '--mes-anterior',
            action='store_true',
            help='Usar el mes anterior completo'
        )
        
        parser.add_argument(
            '--mes',
            type=int,
            help='Número del mes (1-12) del año actual'
        )
        
        parser.add_argument(
            '--year',
            type=int,
            help='Año a usar con --mes (por defecto año actual)'
        )
        
        parser.add_argument(
            '--usuario',
            type=str,
            default='Sistema Automático',
            help='Nombre del usuario que solicita el informe'
        )

    def handle(self, *args, **options):
        emails = options['emails']
        usuario = options['usuario']
        
        # Validar emails
        import re
        for email in emails:
            if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
                self.stdout.write(self.style.ERROR(f'❌ Formato de email inválido: {email}'))
                return
        
        # Determinar fechas
        fecha_desde = None
        fecha_hasta = None
        
        if options['mes_actual']:
            fecha_hasta = datetime.now().date()
            fecha_desde = fecha_hasta.replace(day=1)
            self.stdout.write(self.style.SUCCESS(f'📅 Usando mes actual: {fecha_desde} al {fecha_hasta}'))
            
        elif options['mes_anterior']:
            primer_dia_mes_actual = datetime.now().date().replace(day=1)
            ultimo_dia_mes_anterior = primer_dia_mes_actual - timedelta(days=1)
            fecha_hasta = ultimo_dia_mes_anterior
            fecha_desde = fecha_hasta.replace(day=1)
            self.stdout.write(self.style.SUCCESS(f'📅 Usando mes anterior: {fecha_desde} al {fecha_hasta}'))
            
        elif options['mes']:
            mes = options['mes']
            year = options.get('year', datetime.now().year)
            
            if mes < 1 or mes > 12:
                self.stdout.write(self.style.ERROR('❌ El mes debe estar entre 1 y 12'))
                return
            
            fecha_desde = datetime(year, mes, 1).date()
            # Último día del mes
            if mes == 12:
                fecha_hasta = datetime(year, 12, 31).date()
            else:
                fecha_hasta = datetime(year, mes + 1, 1).date() - timedelta(days=1)
            
            self.stdout.write(self.style.SUCCESS(f'📅 Usando mes {mes}/{year}: {fecha_desde} al {fecha_hasta}'))
            
        elif options['fecha_desde'] and options['fecha_hasta']:
            try:
                fecha_desde = datetime.strptime(options['fecha_desde'], '%Y-%m-%d').date()
                fecha_hasta = datetime.strptime(options['fecha_hasta'], '%Y-%m-%d').date()
                self.stdout.write(self.style.SUCCESS(f'📅 Usando período personalizado: {fecha_desde} al {fecha_hasta}'))
            except ValueError:
                self.stdout.write(self.style.ERROR('❌ Formato de fecha inválido. Usar YYYY-MM-DD'))
                return
        else:
            # Por defecto, mes actual
            fecha_hasta = datetime.now().date()
            fecha_desde = fecha_hasta.replace(day=1)
            self.stdout.write(self.style.WARNING(f'⚠️  No se especificó período, usando mes actual por defecto: {fecha_desde} al {fecha_hasta}'))
        
        # Validar que fecha_desde sea anterior a fecha_hasta
        if fecha_desde > fecha_hasta:
            self.stdout.write(self.style.ERROR('❌ La fecha de inicio debe ser anterior a la fecha de fin'))
            return
        
        # Mostrar información
        self.stdout.write(self.style.SUCCESS('━' * 60))
        self.stdout.write(self.style.SUCCESS('📊 ENVIANDO INFORME DE CONSUMO DE COMBUSTIBLE'))
        self.stdout.write(self.style.SUCCESS('━' * 60))
        self.stdout.write(f'📧 Destinatarios: {", ".join(emails)}')
        self.stdout.write(f'📅 Período: {fecha_desde.strftime("%d/%m/%Y")} al {fecha_hasta.strftime("%d/%m/%Y")}')
        self.stdout.write(f'👤 Solicitado por: {usuario}')
        self.stdout.write(self.style.SUCCESS('━' * 60))
        
        # Enviar el informe (de forma síncrona en el comando)
        self.stdout.write('⏳ Generando y enviando informe...')
        
        try:
            # Llamar directamente a la función (sin thread, ya que el comando es síncrono)
            enviar_informe_combustible_thread(emails, fecha_desde, fecha_hasta, usuario)
            
            self.stdout.write(self.style.SUCCESS('━' * 60))
            self.stdout.write(self.style.SUCCESS('✅ Informe enviado exitosamente'))
            self.stdout.write(self.style.SUCCESS('━' * 60))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR('━' * 60))
            self.stdout.write(self.style.ERROR(f'❌ Error al enviar el informe: {str(e)}'))
            self.stdout.write(self.style.ERROR('━' * 60))
            import traceback
            traceback.print_exc()
