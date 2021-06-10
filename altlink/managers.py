from django.db import models

from .utils import if_object_creation_inside_timedelta

class AlterArticleQuerySet(models.QuerySet):
    def visible(self):
        return self.filter(has_slug=True)

    def category(self, category):
        return self.filter(category_article__name=category)

    def tag(self, tag):
        return self.filter(tag__name=tag)

    def last_timeframe(self, timedelta):
        return self.filter()
    
    def score(self, score_name):
        if score_name == 'new':
            return self.order_by('-timestamp_created')
        else:
            # cutom lookup filter idea from here https://django-filter.readthedocs.io/en/stable/ref/filters.html#method
            # and here https://stackoverflow.com/a/38778107   https://stackoverflow.com/a/7216395
            lookup = '__'.join([str(score_name+'_score'), 'gt'])
            return self.filter( **{lookup: 0} ).order_by('-' + score_name + '_score')

class AlterArticleManager(models.Manager):
    def get_queryset(self):
        return AlterArticleQuerySet(self.model, using=self._db)
    
    def visible(self):
        return self.get_queryset().visible()
    
    def category(self, category):
        return self.get_queryset().category(category)
    
    def tag(self, tag):
        return self.get_queryset().tag(tag)

    def score(self, score_name='hot'):
        return self.get_queryset().score(score_name)