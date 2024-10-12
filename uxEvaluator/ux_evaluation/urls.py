from django.urls import path
from . import views  # Importa las vistas desde tu archivo views.py

urlpatterns = [
    path('index/', views.index, name='index'),  # Ruta para la vista principal
    path('detalle_evaluacion/<int:software_id>/', views.detalle_evaluacion_view, name='detalle_evaluacion'),
    path('', views.login_view, name='login'),
    path('signup/', views.register_view, name='signup'),
    path('logout/', views.logout_view, name='logout_view'),
    path('evaluar/', views.evaluar, name='evaluar'),  # Ruta para la página de evaluación
    
    # Rutas para el flujo de evaluación
    path('stepper/<int:step>/<int:software_id>/', views.stepper_view, name='stepper'),
    path('stepper/<int:step>/', views.stepper_view, name='stepper'),
    path('resumen/<int:software_id>/', views.resumen_view, name='resumen'),
    
    # Ruta para el resumen temporal antes de confirmar
    path('resumen_temporal/<int:software_id>/', views.resumen_temporal_view, name='resumen_temporal'),

    # Ruta para confirmar y enviar la evaluación
    path('confirmar_enviar/<int:software_id>/', views.confirmar_enviar_view, name='confirmar_enviar'),

    # Ruta para el resumen final después de enviar
    path('resumen/<int:software_id>/', views.resumen_view, name='resumen'),
    
    # Ruta para generar el pdf
    path('generar_pdf/<int:software_id>/', views.generar_pdf, name='generar_pdf'),
]