from django.utils.text import slugify

class SlugService:
    @staticmethod
    def generate_unique_slug(model_class, title: str, slug_field: str = "slug") -> str:
        base_slug = slugify(title)
        slug = base_slug
        counter = 1

        while model_class.objects.filter(**{slug_field: slug}).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        return slug