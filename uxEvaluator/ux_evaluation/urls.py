from django.urls import path
from . import views  # Importa las vistas desde tu archivo views.py

urlpatterns = [
    path('index/', views.index, name='index'),  # Ruta para la vista principal
    path('', views.login_view, name='login'),
    path('signup/', views.register_view, name='signup'),
    path('logout/', views.logout_view, name='logout_view'),
    path('evaluar/', views.evaluar, name='evaluar'),  # Ruta para la página de evaluación
    path('stepper/<int:step>/<int:software_id>/', views.stepper_view, name='stepper'),
    path('stepper/<int:step>/', views.stepper_view, name='stepper'),
    path('resumen/<int:software_id>/', views.resumen_view, name='resumen'),
    
]