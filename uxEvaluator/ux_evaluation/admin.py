from django.contrib import admin
from .models import SoftwareEvaluado, Categoria, Criterio, EvaluacionCriterio

# Register your models here.

admin.site.register(SoftwareEvaluado)
admin.site.register(Categoria)
admin.site.register(Criterio)
admin.site.register(EvaluacionCriterio)