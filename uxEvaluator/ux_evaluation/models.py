from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

#Create your models here

class SoftwareEvaluado(models.Model):
    nombre = models.CharField(max_length=255)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha_evaluacion = models.DateTimeField(default=timezone.now) 
    

    def __str__(self):
        return self.nombre

class Categoria(models.Model):
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return self.nombre

class Criterio(models.Model):
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField()

    def __str__(self):
        return self.nombre

class EvaluacionCriterio(models.Model):
    software = models.ForeignKey(SoftwareEvaluado, on_delete=models.CASCADE)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    criterio = models.ForeignKey(Criterio, on_delete=models.CASCADE)
    puntaje = models.IntegerField(choices=[(1, 'Muy Deficiente'), (2, 'Deficiente'), (3, 'Aceptable'), (4, 'Buena'), (5, 'Excelente')])
    comentario = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Evaluación de {self.software.nombre} - {self.categoria.nombre} - {self.criterio.nombre}"
