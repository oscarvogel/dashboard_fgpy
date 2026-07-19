from django.db import models

class Proveedor(models.Model):
    id = models.AutoField(primary_key=True)
    razon_social = models.CharField(max_length=100)
    activo = models.BooleanField()

    class Meta:
        db_table = 'proveedor'  # Ajusta si el nombre real de la tabla es diferente
        managed = False       # Cambia a True si quieres que Django gestione esta tabla con migraciones

class TipoMovil(models.Model):
    id = models.AutoField(primary_key=True)
    descripcion = models.CharField(max_length=50)
    activo = models.BooleanField()

    class Meta:
        db_table = 'tipos_movil'  # Ajusta si el nombre real de la tabla es diferente
        managed = False       # Cambia a True si quieres que Django gestione esta tabla con migraciones

class TipoOperacion(models.Model):
    id = models.AutoField(primary_key=True)
    descripcion = models.CharField(max_length=50)
    activo = models.BooleanField()

    class Meta:
        db_table = 'tipos_operacion'  # Ajusta si el nombre real de la tabla es diferente
        managed = False       # Cambia a True si quieres que Django gestione esta tabla con migraciones
        
class Equipo(models.Model):
    id = models.AutoField(primary_key=True)
    descripcion = models.CharField(max_length=100)
    patente = models.CharField(max_length=10)
    nro_chasis = models.CharField(max_length=30)
    nro_motor = models.CharField(max_length=30)
    capacidad_tanque = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    fecha_adquisicion = models.DateField(null=True, blank=True)
    fecha_baja = models.DateField(null=True, blank=True)
    tipo_movil = models.ForeignKey('TipoMovil', on_delete=models.CASCADE, db_column='tipo_movil_id')
    activo = models.BooleanField()
    observaciones = models.TextField(null=True, blank=True)
    movil_asociado = models.IntegerField()  # Si es una relación autoreferencial, considera usar ForeignKey('self', ...)
    codigo_kobo = models.CharField(max_length=50, unique=True, null=True, blank=True)
    ult_hr_km = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'equipos'  # Ajusta si el nombre real de la tabla es diferente
        managed = False       # Cambia a True si quieres que Django gestione esta tabla con migraciones

class UnidadNegocio(models.Model):
    """
    Modelo no gestionado que mapea la tabla unidades_negocio existente.
    Django no creará/modificará esta tabla (managed=False).
    """
    id = models.AutoField(primary_key=True)
    descripcion = models.TextField(null=True, blank=True)
    prefijo = models.CharField(max_length=10, null=True, blank=True)
    activo = models.BooleanField(default=False)
    codigo_kobo = models.CharField(max_length=50, unique=True, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'unidades_negocio'

    def __str__(self):
        return self.descripcion or f"Unidad {self.id}"

class Empleado(models.Model):
    """
    Modelo no gestionado que mapea la tabla empleados existente.
    Django no creará/modificará esta tabla (managed=False).
    """
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=50)
    email = models.CharField(max_length=255, null=True, blank=True)
    telefono = models.CharField(max_length=50, null=True, blank=True)
    direccion = models.CharField(max_length=200, null=True, blank=True)
    documento = models.CharField(max_length=20, null=True, blank=True)
    fecha_contratacion = models.DateField(null=True, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    fecha_baja = models.DateField(null=True, blank=True)
    activo = models.BooleanField(default=True)
    observaciones = models.TextField(null=True, blank=True)
    porcentaje = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    codigo_kobo = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'empleados'

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

class Paniol(models.Model):
    id = models.AutoField(primary_key=True)
    descripcion = models.CharField(max_length=100)
    activo = models.BooleanField()
    unidad_negocio = models.ForeignKey('UnidadNegocio', on_delete=models.CASCADE, db_column='unidad_negocio_id')

    class Meta:
        db_table = 'panioles'  # Ajusta si el nombre real de la tabla es diferente
        managed = False       # Cambia a True si quieres que Django gestione esta tabla con migraciones

class TipoCombustible(models.Model):
    id = models.AutoField(primary_key=True)
    descripcion = models.CharField(max_length=50)
    activo = models.BooleanField()

    class Meta:
        db_table = 'tipos_combustible'  # Ajusta si el nombre real de la tabla es diferente
        managed = False       # Cambia a True si quieres que Django gestione esta tabla con migraciones

class UnidadProduccion(models.Model):
    id = models.AutoField(primary_key=True)
    descripcion = models.CharField(max_length=100)
    activo = models.BooleanField()

    class Meta:
        db_table = 'unidades_produccion'
        managed = False

    def __str__(self):
        return self.descripcion or f"Unidad {self.id}"
        
class TableroProduccion(models.Model):
    """
    Modelo no gestionado que mapea la tabla tablero_produccion existente.
    Django no creará/modificará esta tabla (managed=False).
    """
    id = models.AutoField(primary_key=True)
    fecha = models.DateField()
    unidad_negocio = models.ForeignKey(
        UnidadNegocio,
        on_delete=models.DO_NOTHING,
        db_column='unidad_negocio_id',
        related_name='producciones'
    )
    empleado_id = models.IntegerField()
    equipo_id = models.IntegerField()
    hr_inicio = models.FloatField(default=0)
    hr_fin = models.FloatField(default=0)
    produccion = models.DecimalField(max_digits=10, decimal_places=2)
    unidad_produccion = models.ForeignKey(
        UnidadProduccion,
        on_delete=models.DO_NOTHING,
        db_column='unidad_produccion_id',
        related_name='producciones'
    )
    observaciones = models.TextField(null=True, blank=True)
    coeficiente = models.DecimalField(max_digits=10, decimal_places=2)
    altura = models.DecimalField(max_digits=10, decimal_places=2)
    ancho = models.DecimalField(max_digits=10, decimal_places=2)
    cantidad_estibas = models.DecimalField(max_digits=10, decimal_places=2)
    largo_madera = models.DecimalField(max_digits=10, decimal_places=2)
    remito = models.IntegerField()
    carros = models.IntegerField()
    hora = models.TimeField()
    turno = models.CharField(max_length=10)
    cliente_id = models.IntegerField()
    plantas = models.IntegerField()
    predio_id = models.IntegerField()
    hrs_no_operativas = models.IntegerField()
    carga_piso = models.IntegerField()
    tipo_operacion = models.ForeignKey(
        TipoOperacion,
        on_delete=models.DO_NOTHING,
        db_column='tipo_operacion_id',
        related_name='producciones'
    )
    lenia_seca = models.IntegerField(default=0)
    carga_rollo = models.IntegerField(default=0)
    carga_lenia = models.IntegerField(default=0)
    fecha_corte = models.DateField(null=True, blank=True)
    periodo = models.CharField(max_length=6)
    tarifa = models.FloatField()
    tarifa_empresa = models.FloatField()
    origen_destino_id = models.IntegerField()
    tabla = models.CharField(max_length=50, null=True, blank=True)
    codigo_tabla = models.IntegerField()
    origen = models.CharField(max_length=80, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'tablero_produccion'

    def __str__(self):
        return f"Produccion {self.id} - {self.fecha}"

class MovimientoCombustible(models.Model):
    id = models.AutoField(primary_key=True)
    fecha = models.DateField()
    tipo_combustible = models.ForeignKey('TipoCombustible', on_delete=models.CASCADE, db_column='tipo_combustible_id')
    equipo = models.ForeignKey('Equipo', on_delete=models.CASCADE, db_column='equipo_id')
    km_hora = models.FloatField()
    precio_litro = models.DecimalField(max_digits=10, decimal_places=2)
    ingreso = models.DecimalField(max_digits=10, decimal_places=2)
    egreso = models.DecimalField(max_digits=10, decimal_places=2)
    unidad_negocio = models.ForeignKey('UnidadNegocio', on_delete=models.CASCADE, db_column='unidad_negocio_id')
    paniol = models.ForeignKey('Paniol', on_delete=models.CASCADE, db_column='paniol_id', null=True, blank=True)
    remito = models.CharField(max_length=12)
    idtabla = models.IntegerField()
    tabla = models.CharField(max_length=30)
    usuario = models.CharField(max_length=30)
    fecha_grabacion = models.DateTimeField()
    observaciones = models.TextField(blank=True, null=True)
    proveedor = models.ForeignKey('Proveedor', on_delete=models.CASCADE, db_column='proveedor_id', default=1)
    periodo = models.CharField(max_length=6)

    class Meta:
        db_table = 'movimientocombustible'  # Ajusta si tu tabla tiene otro nombre
        managed = False  # Cambia a True si quieres que Django gestione la migración de esta tabla