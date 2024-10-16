# Generated by Django 5.1.2 on 2024-10-12 23:33

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ux_evaluation', '0003_softwareevaluado_fecha_evaluacion'),
    ]

    operations = [
        migrations.CreateModel(
            name='DescripcionPuntaje',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('puntaje', models.IntegerField(choices=[(1, 'Muy Deficiente'), (2, 'Deficiente'), (3, 'Aceptable'), (4, 'Buena'), (5, 'Excelente')])),
                ('descripcion', models.TextField()),
                ('criterio', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ux_evaluation.criterio')),
            ],
        ),
    ]
