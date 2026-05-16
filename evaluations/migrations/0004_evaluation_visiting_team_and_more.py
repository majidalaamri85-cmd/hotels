from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('evaluations', '0003_evaluationimage'),
    ]

    operations = [
        migrations.AddField(
            model_name='evaluation',
            name='additional_person',
            field=models.CharField(blank=True, max_length=255, verbose_name='شخص آخر'),
        ),
        migrations.AddField(
            model_name='evaluation',
            name='visiting_team',
            field=models.CharField(blank=True, max_length=255, verbose_name='الفريق الزائر'),
        ),
    ]