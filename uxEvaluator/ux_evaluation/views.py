from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from collections import defaultdict
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph , Spacer
from reportlab.lib.styles import getSampleStyleSheet
from django.shortcuts import render, redirect, get_object_or_404
from .models import SoftwareEvaluado, Categoria, Criterio, EvaluacionCriterio, DescripcionPuntaje
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages

@login_required
def index(request):
    evaluaciones_por_software = SoftwareEvaluado.objects.filter(usuario=request.user).order_by('-fecha_evaluacion')
    return render(request, 'evaluation/index.html', {
        'evaluaciones_por_software': evaluaciones_por_software
    })


@login_required
def detalle_evaluacion_view(request, software_id):
    software = get_object_or_404(SoftwareEvaluado, id=software_id)
    evaluaciones = software.evaluacioncriterio_set.all()
    categorias = {}
    for evaluacion in evaluaciones:
        categoria_nombre = evaluacion.categoria.nombre
        if categoria_nombre not in categorias:
            categorias[categoria_nombre] = []
        categorias[categoria_nombre].append(evaluacion)
    return render(request, 'evaluation/detalle_evaluacion.html', {
        'software': software,
        'categorias': categorias
    })
    
def eliminar_evaluacion(request, software_id):
    software = get_object_or_404(SoftwareEvaluado, id=software_id)

    if request.method == 'POST':
        # Eliminar el software evaluado
        software.delete()
        return redirect('index')  # Redirige a la página de inicio o a donde desees

    # Si no es POST, redirige o muestra un error
    return redirect('detalle_evaluacion', software_id=software.id)


def login_view(request):
    if request.user.is_authenticated:
        return redirect('index')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('index')
    else:
        form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('index')
    
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def stepper_view(request, step=1, software_id=None):
    if step == 1:
        return handle_software_name_step(request)

    software = get_software_or_redirect(software_id)
    categorias = Categoria.objects.all()
    if not categorias.exists():
        return render(request, 'evaluation/stepper.html', {
            'error': 'No hay categorías disponibles para evaluar.',
        })

    if step-1 > len(categorias):
        return redirect('resumen_temporal', software_id=software.id)

    categoria_actual = categorias[step - 2]
    criterios = Criterio.objects.filter(categoria=categoria_actual)
    if not criterios.exists():
        return render(request, 'evaluation/stepper.html', {
            'error': f'No hay criterios disponibles para la categoría {categoria_actual.nombre}.',
            'step': step,
            'software': software,
            'categoria': categoria_actual,
            'categorias_totales': categorias.count(),
        })
    if request.method == 'POST':
        return handle_evaluation_post(request, software, categoria_actual, criterios, step)

    descripciones_puntajes = {}
    for criterio in criterios:
        descripciones_puntajes[criterio.id] = DescripcionPuntaje.objects.filter(criterio=criterio)
        
    iconos_y_descripciones = {
        1: {
            'icono': 'fa-user-check',
            'descripcion': 'La usabilidad en UX mide qué tan fácil e intuitivo es para los usuarios interactuar con un producto digital. Se enfoca en que los usuarios puedan realizar tareas de manera eficiente, sin errores y con una experiencia satisfactoria. Un buen diseño usable facilita el aprendizaje, mejora la eficiencia y reduce la frustración, asegurando que el producto sea accesible y agradable de utilizar.',
        },
        2: {
            'icono': 'fa-wheelchair',
            'descripcion': 'La accesibilidad en UX se refiere a la capacidad de un producto digital para ser utilizado por personas con diversas capacidades o discapacidades. Un diseño accesible garantiza que todos los usuarios, independientemente de sus limitaciones físicas, sensoriales o cognitivas, puedan interactuar y beneficiarse del sistema. Esto incluye el uso de tecnologías asistivas, interfaces claras y adaptaciones para garantizar que el producto sea inclusivo para todos.',
        },
        3: {
            'icono': 'fa-lightbulb',
            'descripcion': 'La simplicidad en UX se refiere a un diseño limpio y directo, que reduce la complejidad innecesaria para que los usuarios puedan completar sus tareas de manera rápida y sin distracciones. Un diseño simple elimina elementos innecesarios y se enfoca en lo esencial, facilitando la navegación y mejorando la experiencia del usuario.',
        },
        4: {
            'icono': 'fa-sync-alt',
            'descripcion': 'La consistencia en UX se refiere a la uniformidad en el diseño y la interacción a través de una aplicación o sitio web. Incluye elementos como colores, tipografías, y patrones de navegación. Una experiencia coherente facilita la usabilidad, reduce la carga cognitiva, aumenta la confianza del usuario y refuerza la identidad de la marca.',
        },
        5: {
            'icono': 'fa-users',
            'descripcion': 'El centrado en el usuario en UX es un enfoque de diseño que prioriza las necesidades, comportamientos y expectativas de los usuarios finales. Implica investigar y comprender a los usuarios a través de métodos como entrevistas, encuestas y pruebas de usabilidad. Este enfoque asegura que las decisiones de diseño se basen en la experiencia real del usuario, mejorando la satisfacción y la efectividad del producto final. ',
        },
        
    }

    return render(request, 'evaluation/stepper.html', {
        'step': step,
        'software': software,
        'categoria': categoria_actual,
        'criterios': criterios,
        'categorias_totales': categorias.count(),
        'evaluaciones': request.session.get('evaluaciones', {}),
        'icono': iconos_y_descripciones[step-1]['icono'],
        'descripcion': iconos_y_descripciones[step-1]['descripcion'],
        'descripciones_puntajes': descripciones_puntajes
        })


def resumen_temporal_view(request, software_id):
    software = get_object_or_404(SoftwareEvaluado, id=software_id)
    evaluaciones = request.session.get('evaluaciones', {})
    categorias = {}
    for categoria_id, criterios in evaluaciones.items():
        try:
            categoria_id_int = int(categoria_id)
        except ValueError:
            messages.error(request, f'ID de categoría no válido: {categoria_id}')
            return redirect('index')

        categoria = get_object_or_404(Categoria, id=categoria_id_int)
        categorias[categoria] = []
        for criterio_id, evaluacion in criterios.items():
            if criterio_id == 'puntaje' or criterio_id == 'comentario':
                continue  # Ignorar entradas incorrectas

            try:
                criterio_id_int = int(criterio_id)
            except ValueError:
                messages.error(request, f'ID de criterio no válido: {criterio_id}')
                return redirect('index')

            criterio = get_object_or_404(Criterio, id=criterio_id_int)
            categorias[categoria].append({
                'criterio': criterio,
                'puntaje': evaluacion['puntaje'],
                'comentario': evaluacion['comentario']
            })

    return render(request, 'evaluation/resumen_temporal.html', {
        'software': software,
        'categorias': categorias
    })


def confirmar_enviar_view(request, software_id):
    software = get_object_or_404(SoftwareEvaluado, id=software_id)
    evaluaciones = request.session.get('evaluaciones', {})

    for categoria_id, criterios in evaluaciones.items():
        try:
            categoria_id_int = int(categoria_id)
        except ValueError:
            messages.error(request, f'ID de categoría no válido: {categoria_id}')
            return redirect('index')

        categoria = get_object_or_404(Categoria, id=categoria_id_int)
        for criterio_id, evaluacion in criterios.items():
            if criterio_id == 'puntaje' or criterio_id == 'comentario':
                continue  # Ignorar entradas incorrectas

            try:
                criterio_id_int = int(criterio_id)
            except ValueError:
                messages.error(request, f'ID de criterio no válido: {criterio_id}')
                return redirect('index')

            criterio = get_object_or_404(Criterio, id=criterio_id_int)
            EvaluacionCriterio.objects.create(
                software=software,
                categoria=categoria,
                criterio=criterio,
                puntaje=evaluacion['puntaje'],
                comentario=evaluacion['comentario']
            )

    # Limpiar las evaluaciones de la sesión después de guardarlas
    request.session['evaluaciones'] = {}
    messages.success(request, 'Evaluación enviada correctamente.')
    return generar_pdf(request, software.id)


def handle_software_name_step(request):
    if request.method == 'POST':
        software_nombre = request.POST.get('software_nombre')
        if software_nombre:
            software = SoftwareEvaluado.objects.create(nombre=software_nombre, usuario=request.user)
            return redirect('stepper', step=2, software_id=software.id)
        else:
            return render(request, 'evaluation/stepper.html', {
                'step': 1,
                'error': 'Por favor, ingresa un nombre de software.'
            })
    return render(request, 'evaluation/stepper.html', {'step': 1})


def get_software_or_redirect(software_id):
    if not software_id:
        return redirect('index')
    return get_object_or_404(SoftwareEvaluado, id=software_id)


def handle_evaluation_post(request, software, categoria_actual, criterios, step):
    evaluaciones = request.session.get('evaluaciones', {})
    if str(categoria_actual.id) not in evaluaciones:
        evaluaciones[str(categoria_actual.id)] = {}

    for criterio in criterios:
        puntaje = request.POST.get(f'evaluacion_{criterio.id}')
        comentario = request.POST.get(f'comentario_{criterio.id}')
        if puntaje:
            try:
                puntaje_int = int(puntaje)
            except ValueError:
                messages.error(request, f'El puntaje para el criterio {criterio.nombre} no es válido.')
                return redirect('stepper', step=step, software_id=software.id)
            
            evaluaciones[str(categoria_actual.id)][str(criterio.id)] = {
                'puntaje': puntaje_int,
                'comentario': comentario
            }

    request.session['evaluaciones'] = evaluaciones
    return redirect('stepper', step=step + 1, software_id=software.id)

@login_required
def generar_pdf(request, software_id):
    software = get_object_or_404(SoftwareEvaluado, id=software_id)
    evaluaciones = EvaluacionCriterio.objects.filter(software=software).order_by('categoria')

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{software.nombre}_evaluacion.pdf"'

    doc = SimpleDocTemplate(response, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    # Título del documento
    title = Paragraph(f"Evaluación de Diseño UX: {software.nombre}", styles['Title'])
    elements.append(title)

    # Agrupar evaluaciones por categoría
    categoria_actual = None
    data = [['Criterio', 'Puntaje', 'Comentario']]  # Encabezado común para todas las tablas
    total_puntaje_categoria = 0  # Inicializar el puntaje de la categoría
    evaluaciones_categoria = 0  # Contador de evaluaciones en la categoría

    for evaluacion in evaluaciones:
        if categoria_actual != evaluacion.categoria:
            # Si cambiamos de categoría, creamos una nueva tabla y encabezado de categoría
            if categoria_actual is not None:
                # Agregar la tabla de la categoría anterior
                table = Table(data)
                style = TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#465362")),  # Encabezado oscuro
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),  # Bordes
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),  # Color de fondo para las filas
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                ])
                table.setStyle(style)
                elements.append(Spacer(1, 12))  # Espacio entre tablas
                elements.append(table)

                # Cálculo del promedio o total y clasificar el resultado
                promedio = total_puntaje_categoria / evaluaciones_categoria
                if promedio >= 4:
                    resultado = "Bueno"
                elif promedio >= 3:
                    resultado = "Regular"
                elif promedio >= 2:
                    resultado = "Malo"
                else:
                    resultado = "Muy malo"

                # Agregar el texto debajo de la tabla con el puntaje total y la clasificación
                elements.append(Paragraph(f"Total puntaje: {total_puntaje_categoria} - Resultado: {resultado}", styles['Normal']))
                elements.append(Spacer(1, 12))  # Espacio antes de la siguiente categoría

            # Título de la nueva categoría
            categoria_actual = evaluacion.categoria
            categoria_title = Paragraph(f"Categoría: {categoria_actual.nombre}", styles['Heading2'])
            elements.append(categoria_title)

            # Reiniciar los datos de la nueva tabla y contadores
            data = [['Criterio', 'Puntaje', 'Comentario']]
            total_puntaje_categoria = 0
            evaluaciones_categoria = 0

        # Añadir filas con los datos de cada evaluación
        data.append([
            evaluacion.criterio.nombre,
            evaluacion.puntaje,
            evaluacion.comentario or 'N/A'
        ])

        # Sumar el puntaje de la categoría actual
        total_puntaje_categoria += evaluacion.puntaje
        evaluaciones_categoria += 1

    # Asegurarse de agregar la última tabla restante
    if data:
        table = Table(data)
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#465362")),  # Encabezado oscuro
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),  # Bordes
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),  # Color de fondo para las filas
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ])
        table.setStyle(style)
        elements.append(Spacer(1, 12))
        elements.append(table)

        # Cálculo del promedio o total para la última categoría y clasificación
        promedio = total_puntaje_categoria / evaluaciones_categoria
        if promedio >= 4:
            resultado = "Bueno"
        elif promedio >= 3:
            resultado = "Regular"
        elif promedio >= 2:
            resultado = "Malo"
        else:
            resultado = "Muy malo"

        # Agregar el texto debajo de la última tabla con el puntaje total y la clasificación
        elements.append(Paragraph(f"Total puntaje: {total_puntaje_categoria} - Resultado: {resultado}", styles['Normal']))

    # Construir el PDF
    doc.build(elements, onFirstPage=lambda canvas, doc: set_metadata(canvas, software.nombre))
    return response

def set_metadata(canvas, title):
    canvas.setTitle(f'Evaluaccion de {title}')
    canvas.setAuthor('UX Evaluator')
    canvas.setSubject(f"Evaluación de Diseño UX de {title}")