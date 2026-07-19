#!/usr/bin/env python
"""
Script de ejemplo para probar el sistema de informes de combustible.

Antes de ejecutar:
1. Activar el entorno virtual
2. pip install -r requirements.txt
3. Configurar las variables de email en settings.py o .env

Ejecutar desde el directorio backend/:
    python test_informe_combustible.py
"""

import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from datetime import datetime, timedelta
from api.views import analizar_consumo_combustible_por_equipo, generar_html_informe_combustible, generar_excel_informe_combustible


def test_analisis():
    """Prueba el análisis de datos sin enviar email"""
    print("=" * 70)
    print("🧪 PRUEBA: Análisis de Consumo de Combustible")
    print("=" * 70)
    
    # Usar el mes actual
    fecha_hasta = datetime.now().date()
    fecha_desde = fecha_hasta.replace(day=1)
    
    print(f"\n📅 Período: {fecha_desde.strftime('%d/%m/%Y')} al {fecha_hasta.strftime('%d/%m/%Y')}")
    print("\n⏳ Analizando datos...")
    
    try:
        datos = analizar_consumo_combustible_por_equipo(fecha_desde, fecha_hasta)
        
        print("\n✅ Análisis completado exitosamente!")
        print("\n📊 RESULTADOS:")
        print("-" * 70)
        print(f"  Consumo total:           {datos['totales']['consumo_total']:,.2f} L")
        print(f"  Horas/Km totales:        {datos['totales']['horas_km_total']:,.2f}")
        print(f"  Equipos activos:         {datos['totales']['equipos_activos']}")
        print(f"  Equipos con alerta:      {datos['totales']['equipos_con_alerta']}")
        print(f"  Total de cargas:         {datos['totales']['total_cargas']}")
        print("-" * 70)
        
        if datos['equipos']:
            print("\n🚜 TOP 5 EQUIPOS POR CONSUMO:")
            print("-" * 70)
            for i, eq in enumerate(datos['equipos'][:5], 1):
                alerta = "⚠️  " if eq['es_elevado'] else "   "
                print(f"{alerta}{i}. {eq['nombre']:<30} {eq['consumo_mes']:>10,.2f} L")
            print("-" * 70)
        
        if datos['alertas']:
            print("\n🚨 ALERTAS DE CONSUMO ELEVADO:")
            print("-" * 70)
            for alerta in datos['alertas']:
                print(f"  ⚠️  {alerta['equipo']} ({alerta['patente']})")
                print(f"      Consumo/hora mes actual: {alerta['consumo_por_hora_actual']:,.2f} L/hr")
                print(f"      Promedio L/hr (últimos 6 meses): {alerta['promedio_ltrs_hora']:,.2f} L/hr")
                print(f"      Diferencia: +{alerta['diferencia_porcentual']}%")
                print()
            print("-" * 70)
        else:
            print("\n✅ No se detectaron consumos elevados (equipos con L/hr >20% sobre promedio)")
        
        return datos
        
    except Exception as e:
        print(f"\n❌ Error en el análisis: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def test_generar_html(datos):
    """Prueba la generación del HTML"""
    print("\n" + "=" * 70)
    print("🧪 PRUEBA: Generación de HTML")
    print("=" * 70)
    
    try:
        print("\n⏳ Generando HTML...")
        html = generar_html_informe_combustible(datos)
        
        # Guardar HTML en un archivo temporal
        filename = f"informe_combustible_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        filepath = os.path.join(os.path.dirname(__file__), filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"\n✅ HTML generado exitosamente!")
        print(f"📄 Archivo guardado en: {filepath}")
        print(f"📏 Tamaño: {len(html):,} bytes")
        print("\n💡 Abre el archivo en un navegador para ver el informe")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error generando HTML: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_generar_excel(datos):
    """Prueba la generación del Excel"""
    print("\n" + "=" * 70)
    print("🧪 PRUEBA: Generación de Excel")
    print("=" * 70)
    
    try:
        print("\n⏳ Generando Excel...")
        excel_file = generar_excel_informe_combustible(datos)
        
        # Guardar Excel en un archivo temporal
        filename = f"informe_combustible_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        filepath = os.path.join(os.path.dirname(__file__), filename)
        
        with open(filepath, 'wb') as f:
            f.write(excel_file.read())
        
        print(f"\n✅ Excel generado exitosamente!")
        print(f"📄 Archivo guardado en: {filepath}")
        print("\n💡 Abre el archivo en Excel para ver los datos")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error generando Excel: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "=" * 70)
    print("🚀 SISTEMA DE PRUEBA - INFORME DE COMBUSTIBLE")
    print("=" * 70)
    
    # Prueba 1: Análisis de datos
    datos = test_analisis()
    
    if not datos:
        print("\n❌ No se pudo completar el análisis. Abortando pruebas.")
        return
    
    # Prueba 2: Generación de HTML
    test_generar_html(datos)
    
    # Prueba 3: Generación de Excel
    test_generar_excel(datos)
    
    print("\n" + "=" * 70)
    print("✅ PRUEBAS COMPLETADAS")
    print("=" * 70)
    print("\n📝 NOTAS:")
    print("  • Los archivos HTML y Excel se han guardado en el directorio backend/")
    print("  • Para enviar emails, usa el comando de Django o el endpoint API")
    print("  • Consulta docs/informe-combustible.md para más información")
    print("\n💡 SIGUIENTE PASO:")
    print("  Prueba enviar un email con:")
    print("  python manage.py enviar_informe_combustible --emails tu-email@ejemplo.com --mes-actual")
    print()


if __name__ == '__main__':
    main()
