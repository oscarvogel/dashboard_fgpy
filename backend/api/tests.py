import json
from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.conf import settings
from django.test import Client, RequestFactory, SimpleTestCase, TestCase
from django.urls import reverse

from .views import _dashboard_finalize_segments, _dashboard_monthly_progress, _dashboard_severity


class AuthCsrfTests(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='secret123',
        )

    def _csrf_token(self):
        response = self.client.get(reverse('api_csrf'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(settings.CSRF_COOKIE_NAME, response.cookies)
        return response.cookies[settings.CSRF_COOKIE_NAME].value

    def test_csrf_endpoint_sets_cookie(self):
        token = self._csrf_token()

        self.assertTrue(token)

    def test_login_requires_csrf_token(self):
        response = self.client.post(
            reverse('api_login'),
            data=json.dumps({'username': 'testuser', 'password': 'secret123'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 403)

    def test_login_with_csrf_token_succeeds(self):
        token = self._csrf_token()

        response = self.client.post(
            reverse('api_login'),
            data=json.dumps({'username': 'testuser', 'password': 'secret123'}),
            content_type='application/json',
            HTTP_X_CSRFTOKEN=token,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['username'], 'testuser')

    def test_profile_update_requires_csrf_token(self):
        self.client.force_login(self.user)

        response = self.client.put(
            reverse('api_user'),
            data=json.dumps({'email': 'updated@example.com'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 403)

    def test_profile_update_with_csrf_token_succeeds(self):
        self.client.force_login(self.user)
        token = self._csrf_token()

        response = self.client.put(
            reverse('api_user'),
            data=json.dumps({'email': 'updated@example.com'}),
            content_type='application/json',
            HTTP_X_CSRFTOKEN=token,
        )

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'updated@example.com')


class DashboardEjecutivoCalculationTests(TestCase):
    def test_dashboard_severity_thresholds(self):
        self.assertEqual(_dashboard_severity(119, 100, 10, 20), ('amarillo', 19.0))
        self.assertEqual(_dashboard_severity(121, 100, 10, 20), ('rojo', 21.0))
        self.assertEqual(_dashboard_severity(87, 100, 8, 15, direction='lower'), ('amarillo', 13.0))
        self.assertEqual(_dashboard_severity(80, 100, 8, 15, direction='lower'), ('rojo', 20.0))
        self.assertEqual(_dashboard_severity(10, 0, 10, 20), ('sin_historico', 0))

    def test_dashboard_keeps_incompatible_units_separated(self):
        segments = {
            (1, 1, 5, 10): {
                'unidad_negocio_id': 1,
                'unidad_negocio': 'Biomasa',
                'tipo_operacion_id': 1,
                'tipo_operacion': 'CHIPEADO',
                'unidad_produccion_id': 5,
                'unidad_produccion': 'Toneladas',
                'equipo_id': 10,
                'equipo': 'Equipo 10',
                'produccion': 100,
                'horas': 10,
                'horas_no_operativas': 0,
                'combustible': 50,
                'registros': 1,
                'dias': {'2026-05-01'},
            },
            (1, 1, 4, 10): {
                'unidad_negocio_id': 1,
                'unidad_negocio': 'Biomasa',
                'tipo_operacion_id': 1,
                'tipo_operacion': 'CHIPEADO',
                'unidad_produccion_id': 4,
                'unidad_produccion': 'Horas',
                'equipo_id': 10,
                'equipo': 'Equipo 10',
                'produccion': 8,
                'horas': 8,
                'horas_no_operativas': 0,
                'combustible': 20,
                'registros': 1,
                'dias': {'2026-05-01'},
            },
        }

        finalized, _ = _dashboard_finalize_segments(segments, {})

        self.assertEqual(len(finalized), 2)
        self.assertEqual({item['unidad_produccion'] for item in finalized}, {'Toneladas', 'Horas'})
        toneladas = next(item for item in finalized if item['unidad_produccion'] == 'Toneladas')
        horas = next(item for item in finalized if item['unidad_produccion'] == 'Horas')
        self.assertEqual(toneladas['metric_label'], 'Prod/hora')
        self.assertEqual(horas['metric_label'], 'Horas/día')

    def test_dashboard_does_not_alert_trucks_without_hours(self):
        segments = {
            (1, 21, 5, 66): {
                'unidad_negocio_id': 1,
                'unidad_negocio': 'Transporte Rollos',
                'tipo_operacion_id': 21,
                'tipo_operacion': 'TRANSPORTE',
                'unidad_produccion_id': 5,
                'unidad_produccion': 'Toneladas',
                'equipo_id': 66,
                'equipo': 'Tracto Camion',
                'tipo_movil': 'CAMION',
                'produccion': 100,
                'horas': 0,
                'horas_no_operativas': 0,
                'combustible': 0,
                'registros': 1,
                'dias': {'2026-05-01'},
            },
        }

        finalized, alertas = _dashboard_finalize_segments(segments, {})

        self.assertEqual(alertas, [])
        self.assertEqual(finalized[0]['metric_label'], 'Toneladas/día')
        self.assertTrue(finalized[0]['omite_metricas_horas'])


class ProduccionDeleteTests(SimpleTestCase):
    def test_delete_produccion_deletes_linked_combustible(self):
        from .views import api_produccion_delete

        request = RequestFactory().delete('/api/produccion/42/')
        request.user = SimpleNamespace(is_authenticated=True)
        produccion = Mock()
        produccion.id = 42
        produccion.delete.return_value = (1, {'api.TableroProduccion': 1})
        combustible_qs = Mock()
        combustible_qs.delete.return_value = (1, {'api.MovimientoCombustible': 1})

        with patch('api.views.transaction.atomic', return_value=nullcontext()), \
                patch('api.views.TableroProduccion.objects.get', return_value=produccion) as get_produccion, \
                patch('api.views.MovimientoCombustible.objects.filter', return_value=combustible_qs) as filter_combustible:
            response = api_produccion_delete(request, 42)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), {
            'detail': 'Movimiento eliminado',
            'produccion_id': 42,
            'combustible_eliminados': 1,
        })
        get_produccion.assert_called_once_with(id=42)
        filter_combustible.assert_called_once_with(idtabla=42)
        combustible_qs.delete.assert_called_once_with()
        produccion.delete.assert_called_once_with()
