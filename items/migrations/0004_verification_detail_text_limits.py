from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("items", "0003_founditem_disposal")]

    operations = [
        migrations.AlterField(
            model_name="verificationdetail",
            name="serial_no",
            field=models.CharField(blank=True, max_length=500, verbose_name="Serial number"),
        ),
        migrations.AlterField(
            model_name="verificationdetail",
            name="marks",
            field=models.TextField(blank=True, help_text="Scratches, stickers, a torn corner.", max_length=500, verbose_name="Marks"),
        ),
        migrations.AlterField(
            model_name="verificationdetail",
            name="contents",
            field=models.TextField(blank=True, help_text="e.g. student ID, two keys.", max_length=500, verbose_name="What is inside it"),
        ),
    ]
