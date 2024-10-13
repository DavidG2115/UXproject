from django.contrib import admin
from .models import SoftwareEvaluado, Categoria, Criterio, EvaluacionCriterio, DescripcionPuntaje

# Register your models here.

admin.site.register(SoftwareEvaluado)
admin.site.register(Categoria)
admin.site.register(Criterio)
admin.site.register(EvaluacionCriterio)
admin.site.register(DescripcionPuntaje)