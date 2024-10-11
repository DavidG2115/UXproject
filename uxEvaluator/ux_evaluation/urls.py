from django.urls import path
from . import views  # Importa las vistas desde tu archivo views.py

urlpatterns = [
    path('', views.index, name='index'),  # Ruta para la vista principal
    path('evaluar/', views.evaluar, name='evaluar'),  # Ruta para la página de evaluación
    path('stepper/<int:step>/<int:software_id>/', views.stepper_view, name='stepper'),
    path('stepper/<int:step>/', views.stepper_view, name='stepper'),
    path('resumen/<int:software_id>/', views.resumen_view, name='resumen'),
]