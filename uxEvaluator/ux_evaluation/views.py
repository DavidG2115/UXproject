
from django.shortcuts import render, redirect, get_object_or_404
from .models import SoftwareEvaluado, Categoria, Criterio, EvaluacionCriterio


def index(request):
    return render(request, 'index.html')  #

def evaluar(request):
    return render(request, 'templates/evaluar.html')  # 

from django.shortcuts import render, redirect, get_object_or_404
from .models import SoftwareEvaluado, Categoria, Criterio, EvaluacionCriterio

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
        return redirect('resumen', software_id=software.id)

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
        'evaluaciones': request.session.get('evaluaciones', {}),  # Cargar evaluaciones del session
    })


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
