from django.db import IntegrityError, transaction
from django.utils.text import slugify

def save(self, *args, **kwargs):
    if self.slug:
        return super().save(*args, **kwargs)
    
    base_slug = slugify(self.title)
    slug = base_slug
    counter = 1

    while True:
        try:
            with transaction.atomic():
                self.slug = slug 
                return super().save(*args, **kwargs)
        except IntegrityError:
            slug = f"{base_slug}-{counter}"
            counter += 1