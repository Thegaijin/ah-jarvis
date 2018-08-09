from django.db import models
from django.utils.text import slugify
from django.db.models.signals import pre_save
from django.dispatch import receiver
from authors.apps.core.utils import random_string_generator
from authors.apps.core.models import TimeModel


class Article(TimeModel):
    ''' This class represents the Article model '''
    slug = models.SlugField(db_index=True, max_length=255, unique=True)
    title = models.CharField(db_index=True, max_length=255)
    description = models.TextField()
    body = models.TextField()
    author = models.ForeignKey(
                    'profiles.Profile',
                    on_delete=models.CASCADE,
                    related_name='articles')
    # default image for the article.
    image_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.title

class Comment(TimeModel):
    """ Model to represent a Comment. """
    body = models.TextField()

    article = models.ForeignKey(
        'articles.Article', related_name='comments', on_delete=models.CASCADE
    )

    author = models.ForeignKey(
        'profiles.Profile', related_name='comments', on_delete=models.CASCADE
    )

    parent = models.ForeignKey(
        'self', null=True, blank=False, on_delete=models.CASCADE, related_name='thread'
    )

@receiver(pre_save, sender=Article)
def add_slug_to_article_if_not_exists(sender, instance, *args, **kwargs):
    """ create a signal to add slug field if None exists. """
    MAXIMUM_SLUG_LENGTH = 255

    if instance:
        slug = slugify(instance.title)
        unique = random_string_generator()

        if len(slug) > MAXIMUM_SLUG_LENGTH:
            slug = slug[:MAXIMUM_SLUG_LENGTH]

        while len(slug + '-' + unique) > MAXIMUM_SLUG_LENGTH:
            parts = slug.split('-')

            if len(parts) is 1:
                slug = slug[:MAXIMUM_SLUG_LENGTH - len(unique) - 1]
            else:
                slug = '-'.join(parts[:-1])

        instance.slug = slug + '-' + unique
