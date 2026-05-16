from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('evaluations', '0002_alter_criterion_options_alter_evaluation_options_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='EvaluationImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='evaluation_images/general/%Y/%m/', verbose_name='الصورة')),
                ('caption', models.CharField(blank=True, max_length=255, verbose_name='وصف الصورة')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الرفع')),
                ('evaluation', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='general_images', to='evaluations.evaluation', verbose_name='التقييم')),
            ],
            options={
                'verbose_name': 'صورة عامة للتقييم',
                'verbose_name_plural': 'الصور العامة للتقييم',
            },
        ),
    ]
