from django.db import migrations,models



def migrate_is_vegetarian_to_type(apps, schema_editor):
    MenuItem = apps.get_model("staff", "MenuItem")
    for item in MenuItem.objects.all():
        if hasattr(item, 'is_vegetarian'):
            item.type = "Veg" if item.is_vegetarian else "Non Veg"
            item.save()

class Migration(migrations.Migration):

    dependencies = [
        ('staff', '0011_restaurant_template'),
    ]

    operations = [
        migrations.AddField(
            model_name='menuitem',
            name='type',
            field=models.CharField(
                max_length=10,
                choices=[('Veg', 'Veg'), ('Non-Veg', 'Non-Veg'), ('Drink', 'Drink')],
                default='Veg'
            ),
        ),
        migrations.RunPython(migrate_is_vegetarian_to_type),
        migrations.RemoveField(
            model_name='menuitem',
            name='is_vegetarian',
        ),
    ]
