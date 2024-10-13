from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from collections import defaultdict
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from django.shortcuts import render, redirect, get_object_or_404
from .models import SoftwareEvaluado, Categoria, Criterio, EvaluacionCriterio, DescripcionPuntaje
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.decorators import login_required


def index(request):
    evaluaciones_por_software = SoftwareEvaluado.objects.filter(usuario=request.user).order_by('-fecha_evaluacion')
    return render(request, 'evaluation/index.html', {
        'evaluaciones_por_software': evaluaciones_por_software
    })

def evaluacion_view(request):
    return render(request, 'evaluar.html')


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


def login_view(request):
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

    if step > len(categorias):
        return redirect('resumen_temporal', software_id=software.id)

    categoria_actual = categorias[step - 1]
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
            'icono': 'fa-hand-point-up',
            'descripcion': 'Esta categoría se centra en la usabilidad del software.',
        },
        2: {
            'icono': 'fa-cogs',
            'descripcion': 'En esta categoría evaluaremos la funcionalidad del software.',
        },
        3: {
            'icono': 'fa-user',
            'descripcion': 'Aquí se analizará la experiencia del usuario en el software.',
        },
        4: {
            'icono': 'fa-balance-scale',
            'descripcion': 'En esta categoría evaluaremos la accesibilidad del software.',
        },
        5: {
            'icono': 'fa-balance-scale',
            'descripcion': 'En esta categoría evaluaremos la accesibilidad del software.',
        }
    }

    return render(request, 'evaluation/stepper.html', {
        'step': step,
        'software': software,
        'categoria': categoria_actual,
        'criterios': criterios,
        'categorias_totales': categorias.count(),
        'evaluaciones': request.session.get('evaluaciones', {}),
        'icono': iconos_y_descripciones[step]['icono'],
        'descripcion': iconos_y_descripciones[step]['descripcion'],
        'descripciones_puntajes': descripciones_puntajes
        })


def resumen_temporal_view(request, software_id):
    software = get_object_or_404(SoftwareEvaluado, id=software_id)
    evaluaciones = request.session.get('evaluaciones', {})

    categorias = {}
    for categoria_id, criterios in evaluaciones.items():
        categoria = get_object_or_404(Categoria, id=categoria_id)
        for criterio_id, evaluacion in criterios.items():
            criterio = get_object_or_404(Criterio, id=criterio_id)
            if categoria.nombre not in categorias:
                categorias[categoria.nombre] = []
            categorias[categoria.nombre].append({
                'criterio': criterio,
                'puntaje': evaluacion['puntaje'],
                'comentario': evaluacion['comentario'],
            })

    return render(request, 'evaluation/resumen_temporal.html', {
        'software': software,
        'categorias': categorias
    })


def confirmar_enviar_view(request, software_id):
    software = get_object_or_404(SoftwareEvaluado, id=software_id)
    evaluaciones = request.session.get('evaluaciones', {})

    if not evaluaciones:
        return redirect('index')

    for categoria_id, criterios in evaluaciones.items():
        categoria = get_object_or_404(Categoria, id=categoria_id)
        for criterio_id, evaluacion in criterios.items():
            criterio = get_object_or_404(Criterio, id=criterio_id)
            EvaluacionCriterio.objects.create(
                software=software,
                categoria=categoria,
                criterio=criterio,
                puntaje=evaluacion['puntaje'],
                comentario=evaluacion['comentario']
            )

    del request.session['evaluaciones']

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
            evaluaciones[str(categoria_actual.id)][criterio.id] = {
                'puntaje': int(puntaje),
                'comentario': comentario
            }

    request.session['evaluaciones'] = evaluaciones
    return redirect('stepper', step=step + 1, software_id=software.id)


def generar_pdf(request, software_id):
    software = get_object_or_404(SoftwareEvaluado, id=software_id)
    evaluaciones = EvaluacionCriterio.objects.filter(software=software)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{software.nombre}_evaluacion.pdf"'

    doc = SimpleDocTemplate(response, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    title = Paragraph(f"Evaluación de Diseño UX: {software.nombre}", styles['Title'])
    elements.append(title)

    data = [['Categoría', 'Criterio', 'Puntaje', 'Comentario']]
    for evaluacion in evaluaciones:
        row = [
            evaluacion.categoria.nombre,
            evaluacion.criterio.nombre,
            evaluacion.puntaje,
            evaluacion.comentario
        ]
        data.append(row)

    table = Table(data)
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ])
    table.setStyle(style)
    elements.append(table)

    doc.build(elements, onFirstPage=lambda canvas, doc: set_metadata(canvas, software.nombre))
    return response


def set_metadata(canvas, title):
    canvas.setTitle(f'Evaluaccion de {title}')
    canvas.setAuthor('Tu Nombre o Empresa')
    canvas.setSubject(f"Evaluación de Diseño UX de {title}")
    canvas.setCreator('Tu Nombre o Empresa')