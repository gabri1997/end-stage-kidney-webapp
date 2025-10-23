from django.db import migrations, models

def update_esiti(apps, schema_editor):
    Predizione = apps.get_model('prediction', 'Predizione')
    for pred in Predizione.objects.all():
        prob = pred.probabilita_eskd
        if prob >= 70:
            pred.esito = 'ALTO'
        elif prob >= 30:
            pred.esito = 'MEDIO'
        else:
            pred.esito = 'BASSO'
        pred.save()

class Migration(migrations.Migration):

    dependencies = [
        ('prediction', '0005_remove_paziente_iperteso'),
    ]

    operations = [
        migrations.AlterField(
            model_name='predizione',
            name='esito',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('BASSO', 'Basso'),
                    ('MEDIO', 'Medio'),
                    ('ALTO', 'Alto'),
                ]
            ),
        ),
        migrations.RunPython(update_esiti),
    ]