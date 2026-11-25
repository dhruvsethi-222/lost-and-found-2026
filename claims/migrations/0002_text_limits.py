from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("claims", "0001_initial")]

    operations = [
        migrations.AlterField(
            model_name="claim",
            name="answers",
            field=models.TextField(max_length=500),
        ),
    ]
