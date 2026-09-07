"""
One-time data migration: fix image field values so they resolve correctly
via django-cloudinary-storage.

Background
----------
Before Cloudinary was configured, images were stored locally with paths like:
    categories/download.webp
    products/download_1_rxuc4gQ.webp

django-cloudinary-storage stores a bare Cloudinary public_id in the DB field.
When images were re-uploaded through the Django Admin after Cloudinary was
enabled, the files landed at Cloudinary WITHOUT the subfolder prefix, e.g.:
    public_id = "1751553618145-kisna-1.jpg"   (root level)
    URL       = https://res.cloudinary.com/tcelkyco/image/upload/v.../1751553618145-kisna-1.jpg

But the DB field was never updated — it still contains the OLD local path
"categories/1751553618145-kisna-1.jpg", causing url() to build a wrong
Cloudinary URL that 404s.

Fix: strip the leading "categories/" or "products/" folder prefix from any
image field value that starts with those strings, leaving just the filename
as the public_id so Cloudinary resolves it correctly.
"""
from django.db import migrations
import os


STALE_PREFIXES = ('categories/', 'products/')


def _fix_name(name):
    """Strip stale folder prefix if present, return corrected public_id."""
    if not name:
        return name
    for prefix in STALE_PREFIXES:
        if name.startswith(prefix):
            return os.path.basename(name)
    return name


def fix_image_paths(apps, schema_editor):
    Category = apps.get_model('products', 'Category')
    Product = apps.get_model('products', 'Product')

    for cat in Category.objects.exclude(image=''):
        fixed = _fix_name(cat.image.name)
        if fixed != cat.image.name:
            cat.image.name = fixed
            cat.save(update_fields=['image'])

    for prod in Product.objects.all():
        changed = []
        for field in ('image', 'image_2', 'image_3'):
            field_val = getattr(prod, field)
            if field_val:
                fixed = _fix_name(field_val.name)
                if fixed != field_val.name:
                    field_val.name = fixed
                    changed.append(field)
        if changed:
            prod.save(update_fields=changed)


def noop(apps, schema_editor):
    pass  # intentionally irreversible


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0002_initial'),
    ]

    operations = [
        migrations.RunPython(fix_image_paths, noop),
    ]
