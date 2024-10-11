from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from django.shortcuts import render, redirect, get_object_or_404
from .models import SoftwareEvaluado, Categoria, Criterio, EvaluacionCriterio
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.decorators import login_required


def index(request):
    return render(request, 'evaluation/index.html')  #

def evaluar(request):
    return render(request, 'evaluar.html')  # 

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('index')  # Redirigir al home después de iniciar sesión
    else:
        form = AuthenticationForm()
    
    return render(request, 'registration/login.html', {'form': form})


def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()  # Guardar el nuevo usuario
            login(request, user)  # Autenticar y loguear automáticamente al usuario
            return redirect('index')  # Redirigir al home después de registrarse
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
        return redirect('resumen_temporal', software_id=software.id)  # Redirigir al resumen temporal

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

    # Renderizar el template
    return render(request, 'evaluation/stepper.html', {
        'step': step,
        'software': software,
        'categoria': categoria_actual,
        'criterios': criterios,
        'categorias_totales': categorias.count(),
        'evaluaciones': request.session.get('evaluaciones', {}),
    })
    
    
def resumen_temporal_view(request, software_id):
    software = get_object_or_404(SoftwareEvaluado, id=software_id)
    evaluaciones = request.session.get('evaluaciones', {})

    # Cargar las evaluaciones temporales desde la sesión
    evaluaciones_finales = []
    for categoria_id, criterios in evaluaciones.items():
        categoria = get_object_or_404(Categoria, id=categoria_id)
        for criterio_id, evaluacion in criterios.items():
            criterio = get_object_or_404(Criterio, id=criterio_id)
            evaluaciones_finales.append({
                'categoria': categoria.nombre,
                'criterio': criterio.nombre,
                'puntaje': evaluacion['puntaje'],
                'comentario': evaluacion['comentario'],
            })

    return render(request, 'evaluation/resumen_temporal.html', {
        'software': software,
        'evaluaciones': evaluaciones_finales
    })
    
def confirmar_enviar_view(request, software_id):
    software = get_object_or_404(SoftwareEvaluado, id=software_id)
    evaluaciones = request.session.get('evaluaciones', {})

    if not evaluaciones:
        return redirect('index')  # Si no hay evaluaciones, redirigir al index

    # Guardar las evaluaciones en la base de datos
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

    # Limpiar las evaluaciones de la sesión
    del request.session['evaluaciones']

    # Generar el PDF después de enviar la evaluación
    return generar_pdf(request, software.id)  # Asegúrate de usar el ID correcto aquí



def handle_software_name_step(request):
    if request.method == 'POST':
        software_nombre = request.POST.get('software_nombre')
        if software_nombre:
            # Crear un nuevo software cada vez que se envía el nombre
            software = SoftwareEvaluado.objects.create(nombre=software_nombre)
            return redirect('stepper', step=2, software_id=software.id)
        else:
            return render(request, 'evaluation/stepper.html', {
                'step': 1,
                'error': 'Por favor, ingresa un nombre de software.'
            })
    return render(request, 'evaluation/stepper.html', {'step': 1})


def get_software_or_redirect(software_id):
    if not software_id:
        return redirect('index')  # Redirigir si no hay software_id válido
    return get_object_or_404(SoftwareEvaluado, id=software_id)


def handle_evaluation_post(request, software, categoria_actual, criterios, step):
    evaluaciones = request.session.get('evaluaciones', {})
    # Crear una entrada para la categoría actual si no existe
    if str(categoria_actual.id) not in evaluaciones:
        evaluaciones[str(categoria_actual.id)] = {}

    # Guardar los puntajes y comentarios en la sesión
    for criterio in criterios:
        puntaje = request.POST.get(f'evaluacion_{criterio.id}')
        comentario = request.POST.get(f'comentario_{criterio.id}')
        
        if puntaje:
            evaluaciones[str(categoria_actual.id)][criterio.id] = {
                'puntaje': int(puntaje),
                'comentario': comentario
            }
    
    # Almacenar evaluaciones en la sesión
    request.session['evaluaciones'] = evaluaciones

    # Redirigir al siguiente paso
    return redirect('stepper', step=step + 1, software_id=software.id)


    
   
def resumen_view(request, software_id):
    software = get_object_or_404(SoftwareEvaluado, id=software_id)
    evaluaciones = request.session.get('evaluaciones', {})

    for categoria_id, criterios in evaluaciones.items():
        categoria = get_object_or_404(Categoria, id=categoria_id)
        for criterio_id, evaluacion in criterios.items():
            puntaje = evaluacion['puntaje']
            comentario = evaluacion['comentario']
            criterio = get_object_or_404(Criterio, id=criterio_id)

            EvaluacionCriterio.objects.create(
                software=software,
                categoria=categoria,
                criterio=criterio,
                puntaje=puntaje,
                comentario=comentario
            )
    
    # Limpiar las evaluaciones de la sesión después de guardar
    del request.session['evaluaciones']

    evaluaciones_finales = EvaluacionCriterio.objects.filter(software=software)

    return render(request, 'evaluation/resumen.html', {
        'software': software,
        'evaluaciones': evaluaciones_finales
    })

def generar_pdf(request, software_id):
    software = get_object_or_404(SoftwareEvaluado, id=software_id)
    evaluaciones = EvaluacionCriterio.objects.filter(software=software)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{software.nombre}_evaluacion.pdf"'

    # Crear el PDF
    doc = SimpleDocTemplate(response, pagesize=letter)

    # Crear elementos para el PDF
    elements = []

    # Obtener estilos
    styles = getSampleStyleSheet()

    # Título
    title = Paragraph(f"Evaluación de Diseño UX: {software.nombre}", styles['Title'])
    elements.append(title)

    # Crear datos para la tabla
    data = [['Categoría', 'Criterio', 'Puntaje', 'Comentario']]  # Encabezados

    for evaluacion in evaluaciones:
        row = [
            evaluacion.categoria.nombre,
            evaluacion.criterio.nombre,
            evaluacion.puntaje,
            evaluacion.comentario
        ]
        data.append(row)

    # Crear la tabla
    table = Table(data)

    # Estilo de la tabla
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),  # Fondo gris para el encabezado
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),  # Texto blanco en el encabezado
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Centrar texto
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Fuente negrita para el encabezado
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),  # Espacio en el encabezado
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),  # Fondo beige para el resto
        ('GRID', (0, 0), (-1, -1), 1, colors.black),  # Cuadrícula
    ])

    table.setStyle(style)
    elements.append(table)

    # Construir el PDF y establecer metadatos
    doc.build(elements, onFirstPage=lambda canvas, doc: set_metadata(canvas, software.nombre))

    return response

def set_metadata(canvas, title):
    canvas.setTitle(title)  # Cambia 'Anonymous' por el título deseado
    canvas.setAuthor('Tu Nombre o Empresa')  # Cambia por el nombre del autor
    canvas.setSubject(f"Evaluación de Diseño UX de {title}")  # Sujeto del documento
    canvas.setCreator('Tu Nombre o Empresa')  # Cambia por el nombre del creador