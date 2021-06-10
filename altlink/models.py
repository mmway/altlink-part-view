from django.template.defaultfilters import slugify
from django.db import models
from django.db.models import F, Q, Sum, Max, Count, Value as V
from django.db.models.functions import Coalesce
from django.conf import settings
from django.db.models.signals import pre_save, post_save
from django.utils import timezone
from django.dispatch import receiver
from django.urls import reverse
import django.db.models.options as options

from math import sqrt, log

from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy

from datetime import datetime, timedelta


from useralter.models import UserCustomAlter

from django.core.exceptions import ObjectDoesNotExist


from .utils import slug_unique_generator_alter_article, slug_unique_generator_args, get_sentinel_user, get_tags_separate, logger, logger_file, date_seconds_from_fixed_start

from .managers import AlterArticleManager, AlterArticleQuerySet

from .constans import *

# more complex extracting parsing parse of URL domain 
# https://stackoverflow.com/a/44022572/11423556
import tldextract
from urllib.parse import urlparse


# START - upgrading Django ;)
options.DEFAULT_NAMES = options.DEFAULT_NAMES + ('verbose_name_plural_gen','verbose_name_gen',)
# END - upgrading Django ;)

# MODELS
#

class CreatorCanDeleteUpdateMixin(models.Model):

    class Meta:
        abstract = True

    def has_change_permission(self, request, obj=None):
        if obj is not None and obj.user != request.user:
            return False
        return True

    def has_delete_permission(self, request, obj=None):
        if obj is not None and obj.user != request.user:
            return False
        return True

# TO DOlater - add more flags
class Flag(models.Model):
    CHOICES_FLAG_NAME = [
        (None, _('no flag')),
        ('off_topic', _('off topic')),
        ('low_quality', _('poor quality')),
        ('not_credible', _('unreliable source')),
        ('pro', _('should be PRO')),     # post/text/title is more in other direction then already assigned
        ('con', _('should be CON')),     # post/text/title is more in other direction then already assigned
        ('alter', _('should be ALTER')), # post/text/title is more in other direction then already assigned
        ('to_delete', _('to delete')),
        #####################################
        ('spam', _('spam')),
        ('nudity', _('nudity')),
        ('violent', _('too much violence')),
        ('harassing', _('Harassment')),
        ('other', _('other')),
    ]


    name = models.CharField(max_length=20, choices=CHOICES_FLAG_NAME, default=None, blank=True)
    
    # user short description of flagging reason
    # pro,con,alter,url,title,,summary,quote which part violeted etc 
    description = models.CharField(max_length=SETTING_EXCERPT_FIELD_MAX_LENGHT, null=True, blank=True)
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET(get_sentinel_user))
    timestamp_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp_created']

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=SETTING_TAG_FIELD_MAX_LENGHT)

    def __str__(self):
        return self.name

class BannerText(models.Model):
    text = models.CharField(max_length=SETTING_BANNER_TEXT_MAX_LENGHT, blank=False, null=False)
    
    def __str__(self):
        return self.text

# TO DOlater - add more category
class CategoryArticle(models.Model):
    CHOICES_CATEGORY_ARTICLE_NAME = [
        # ('alter', _('alternative')),    # with connection to other second categorie like soft,hardware,music,movie to search for an alternative software, food, solution
        ('business', _('business')),
        ('culture', _('culture')),     # in general articles/cases for topis of movies, theater, music, etc
        ('crypto', _('crypto')),
        ('fun', _('funny')),
        ('food', _('food')),
        ('gossip', _('gossip')),
        # ('hardware', _('hardware')),
        ('health', _('health')),        
        ('history', _('history')),
        ('music', _('music')),
        ('movies', _('movies')),
        ('news', _('news')),
        ('poland', _('Poland')),
        ('politics', _('politics')),
        # ('product', _('product')),
        # ('software', _('software')),
        ('sport', _('sport')),
        ('tech', _('technology')),
        ('world', _('World')),
    ]

    # TO DOlater- max 2-3 choices of category. Tag style categories, 
    # but only 2-3 max of categories that are implemented 
    name = models.CharField(max_length=30, choices=CHOICES_CATEGORY_ARTICLE_NAME, unique=True)
    summary = models.CharField(max_length=300, blank=True, null=True)

    def __str__(self):
        return '{0}'.format(self.get_name_display())

# TO DOlater - add more category
class CategoryDomainWww(models.Model):
    CHOICES_CATEGORY_DOMAIN_NAME = [
        ('politics',_('politics')),
        ('left',_('left')),
        ('right',_('right')),
        ('center',_('center')),
        ('independent',_('independent')),
        ('europe',_('Europe')),
        ('asia',_('Asia')),
        ('usa',_('USA')),
        ('china',_('China')),
        ('russia',_('Russia')),
        ('africa',_('Africa')),
        ('fun',_('funny')),
        ('health',_('health')),
        ('sport',_('sport')),
        ('gossip',_('gossip')),
        ('business',_('business')),
        ('tech',_('technology')),
        ('news',_('news')),
    ]

    # max 2-3 choices of category. Tag style categories, 
    # but only 2-3 max of categories that are implemented 
    name = models.CharField(max_length=30, choices=CHOICES_CATEGORY_DOMAIN_NAME, unique=True)

    def __str__(self):
        return '{0}'.format(self.get_name_display())

class WatchableMixin(models.Model):
    """
    to make models watchable (mark for user watchlist)
    """

    class Meta():
        abstract = True

    def watch_if_user_watched(self, user):
        """
        checks if user mark for wachlist and outpusts True, False, False. Also return 'no' when user is NOT authenticated
        """
        if user.is_authenticated:
            if self.watchlist_users.filter(pk=user.pk).exists():    # if user have already watchlist this object
                return True
            else:
                return False
        return False

class CommentableMixin(models.Model):
    """
    to make models commentable (functions services comments)
    """

    class Meta():
        abstract = True

    @property
    def comments(self):
        """
        return all comments conncected to this instance in order_by('-timestamp_created')
        """
        if hasattr(self, 'contentownercomment'):
            return self.contentownercomment.content_comment.all().order_by('-timestamp_created')
        else:
            return False

# TO DOlater - maybe is better to have a possibility to have AlterArticle
#   to choose if AlterArticle will be 'Pro/Con/Alter' or only 'Alter' to 
#   i.e. alter to some software or product etc. 
#   Not only Pro/Con/Alter to check some links or facts 
# TO DO - many more things
class CounterVotesScoreEnteriesMixin(models.Model):
    """
    to make models votable, enteries inheritance capabilities
    """

    # counters
    entered_counter = models.PositiveIntegerField(default=0, editable=False)  #how many times some users entered from alter-link.com to this domain
    vote_up_counter = models.PositiveIntegerField(default=0, editable=False)
    vote_down_counter = models.PositiveIntegerField(default=0, editable=False)
    vote_score = models.IntegerField(default=0, editable=False)
    best_score = models.DecimalField(default=0, max_digits=9,decimal_places=8)

    # other
    has_slug = models.BooleanField(default=False)

    class Meta():
        abstract = True

    def __str__(self):
        return 'Class: {0}, pk: {1}'.format(self.__class__.__name__, self.pk)

    def best_score_weightning_confidance(self, voteup, votedown):
        vote_up = abs(voteup)
        vote_down = abs(votedown)
        num = vote_up + vote_down
        if num == 0:
            return 0
        z = 1.281551565545
        p = float(vote_up) / num
        left = p + 1/(2*num)*z*z
        right = z*sqrt(p*(1-p)/num + z*z/(4*num*num))
        under = 1+1/num*z*z
        return (left - right) / under

    def update_best_score(self):
        if self.vote_up_counter + self.vote_down_counter == 0:
            self.best_score = 0
        else:
            self.best_score = self.best_score_weightning_confidance(self.vote_up_counter, self.vote_down_counter)


    # TO DO ? - should use F expression
    # https://docs.djangoproject.com/en/2.2/ref/models/expressions/#f-expressions 
    # TO DO ? - in future when there willmi milions of votes?
    # not filtering database after each vote, but only +/- Upvote Downvote one time
    # to not hit database queries after each vote 
    # TO DO ? - need to check if user already voted on this article
    # and then change vote respectively 
    # https://docs.djangoproject.com/en/2.2/ref/models/expressions/#f-expressions 
    # def vote_up_add(self, user_power=1):
    #     self.vote_up_counter = F('vote_up_counter') + user_power
        # self.refresh_from_db()

    # def vote_up_sub(self, user_power=1):
    #     self.vote_up_counter = F('vote_up_counter') - user_power
        # self.refresh_from_db()

    # def vote_down_add(self, user_power=1):
    #     self.vote_down_counter = F('vote_down_counter') + user_power
        # self.refresh_from_db()

    # def vote_down_sub(self, user_power=1):
    #     self.vote_down_counter = F('vote_down_counter') - user_power
        # self.refresh_from_db()

    # aggregation
    # calculate the over queries 
    # https://stackoverflow.com/a/8616400
    # https://docs.djangoproject.com/en/2.2/topics/db/aggregation/
    # TO DO ? - do we have here race condition possible?
    # To DO ? - make signals on Crete() Entered and Votes so after creating there will be updating Counters and scores 
    def update_entered_counter(self):
        self.entered_counter = self.enteries.all().count()
        self.save()
        self.refresh_from_db()
    
    def update_vote_up_counter(self):
        self.vote_up_counter = (
            self.votes.aggregate( votes_up_sum=Coalesce( Sum('value', filter=Q(value__gte=0)), V(0) ) )
            )['votes_up_sum']
        self.save()
        self.refresh_from_db()
    
    def update_vote_down_counter(self):
        self.vote_down_counter = -(
            self.votes.aggregate( votes_down_sum=Coalesce( Sum('value', filter=Q(value__lte=0)), V(0) ) )
            )['votes_down_sum']
        self.save()
        self.refresh_from_db()

    def update_vote_score(self):
        self.vote_score = F('vote_up_counter') - F('vote_down_counter')
        self.save()
        self.refresh_from_db()

    def update_pro_con_alter_score(self):
        if self.__class__.__name__ == 'UrlArticleInfo':
            self.alter_article.update_vote_proconalter_counter(type_url_passed=self.type_url)
        self.save()
        self.refresh_from_db()

    def update_rest_scores(self):
        self.update_best_score()
        self.save()
        self.refresh_from_db()
        if self.__class__.__name__ == 'UrlArticleInfo':
            self.alter_article.update_controversial_score()
            self.alter_article.update_alternative_score()
            self.alter_article.update_hot_score()
        if self.__class__.__name__ == 'AlterArticle':
            self.update_hot_score()
        self.save()
        self.refresh_from_db()


    # vote_hot can be computed dynamically so there will be no additional 
    # field needed in CounterVotesScoreEnteriesMixin, because vote_hot would be only fo AlterArticles only,
    # so it's better to compute it dynamically like:
    # @property
    # def vote_hot(self): 
    #     """
    #     if voting object is AlterArticle so then can be computed rating 'vote_hot'
    #     """
    #     # 0.001 can be any constant just to be sure that we are not dividing by '0', we can
    #     # control vote_hot value with this constant parameter 
    #     if self.__class__.__name__ is AlterArticle.__name__:
    #         return round(self.vote_score * ( 1 / (((timezone.now() - self.timestamp_created).total_seconds())/3600+0.001) ), 2)
    #     else:
    #         print("Object {0} is not an AlterArticle, so it don't have vote_hot property.".format(self))
    #         return None

    def vote_if_user_voted(self, user):
        """
        checks if user voted on instance and outpusts 'up', 'down', 'no'. Also return 'no' when user is NOT authenticated
        """
        if user.is_authenticated:
            user_vote = self.votes.filter(user=user).first()
            if user_vote and user_vote.value > 0:    # if user haven't already voted on this object
                return 'up'
            elif user_vote and user_vote.value < 0:
                return 'down'
            else:
                return 'no'
        return 'no'

    def voteup(self, user):
        qs_user_votes = self.votes.filter(user=user)
        if qs_user_votes.count() < 1:    # if user haven't already voted on this object
            self.votes.create(user=user, value=user.power)
            self.update_vote_up_counter()
            self.update_vote_score()
            self.update_pro_con_alter_score()
            self.update_rest_scores()
        # LOG - elif qs_user_votes.count() > 1 there would be more than one vote on one instance of object 
        # (AlterArticle, DomaninWww etc) so this is wrong
        elif qs_user_votes.count() > 1:
            print('LOG: {0} \nError- creator message: User ({1}) have more than one vote on object (AlterArticle, DomainWww etc) ({2})'.format(timezone.now(), user, self))
        else:
            user_vote = qs_user_votes[0]
            if user_vote.value < 1:
                user_vote.value=user.power
                user_vote.save()
            else:
                user_vote.value=0
                user_vote.save()
            self.update_vote_up_counter()
            self.update_vote_down_counter()
            self.update_vote_score()
            self.update_pro_con_alter_score()
            self.update_rest_scores()

    def votedown(self, user):
        qs_user_votes = self.votes.filter(user=user)
        if qs_user_votes.count() < 1:    # if user haven't already voted on this object
            self.votes.create(user=user, value=-user.power)
            self.update_vote_down_counter()
            self.update_vote_score()
            self.update_pro_con_alter_score()
            self.update_rest_scores()
        elif qs_user_votes.count() > 1:
            print('LOG: {0} \nError- creator message: User ({1}) have more than one vote on object (AlterArticle, DomainWww etc) ({2})'.format(timezone.now(), user, self))
        else:
            user_vote = qs_user_votes[0]
            if user_vote.value > -1:
                user_vote.value=-user.power
                user_vote.save()
            else:
                user_vote.value=0
                user_vote.save()
            self.update_vote_up_counter()
            self.update_vote_down_counter()
            self.update_vote_score()
            self.update_pro_con_alter_score()
            self.update_rest_scores()

    def entered(self, user, request):
        # TO DO - now entries are counting only when user is_authenticated (logged in) but should be also count with AnonymousUser but then for qs_if_user_entry_too_fast_be_counted should be used user IP address - not User credentials
        if request.user.is_authenticated:
            qs_if_user_entry_too_fast_be_counted = self.enteries.filter( 
                Q(user=user) &
                Q(timestamp_created__gt = timezone.now() - timezone.timedelta(hours=SETTING_TIMEDELTA_HOURS_TO_COUNT_AGAIN_USER_LINK_ENTRY))
            )
            if qs_if_user_entry_too_fast_be_counted:
                print('LOG: {0} \nInfo- creator message: User ({1}) link entry to fast (less than {2} hours) to be counted.'.format(timezone.now(), user, SETTING_TIMEDELTA_HOURS_TO_COUNT_AGAIN_USER_LINK_ENTRY))
            else:
                self.enteries.create(user=user)
                self.update_entered_counter()

# TO DOlater - DomainWww def Vote Score liczenie powinno override i być tylko i aż średnią ważoną z użyteczności (usefullness) danego linku w każdym z powiazanych UrlBase. Czyli jeżeli link jest nie przydatny w 10 UrlBase (np usefullness jest poniżej przynajmniej -10pkt w UrlBase) a 1szt UrlBase jest przydatny i np usefullness jest dodatni conajmniej 10pkt to DomainWww "usefulness" = 10*(-1) + 1*(1) = -9
class DomainWww(CounterVotesScoreEnteriesMixin):
    slug = models.SlugField(editable=False, max_length=SETTING_TITLE_SLUG_FIELD_MAX_LENGHT, unique=True)
    url = models.URLField(max_length=SETTING_URL_FIELD_MAX_LENGHT, unique=True)
    name = models.CharField(max_length=SETTING_URL_FIELD_DOMAIN_MAX_LENGHT, unique=False)
    flag = models.ManyToManyField(Flag, blank=True)
    category_domain_www = models.ManyToManyField(CategoryDomainWww, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET(get_sentinel_user))
    timestamp_created = models.DateTimeField('date created', auto_now_add=True)
    tag = models.ManyToManyField(Tag, blank=True)

    times_exists_in_alter_articles = models.PositiveIntegerField(default=0, editable=False)

    # timestamp aka 'date modified' is harder to write, because it has to be changed 
    # not only when DomainWww model will be changed but also when ContentTitle,Summary etc is changing
    # so maybe it isn't so needed right now 
    # timestamp = models.DateTimeField('date modified', auto_now=True)

    # ForeignKeys, ManyToMany, OneToOne fields attached from other models
    # ContentTitle ??? not needed - only url
    # ContentSummary 

    class Meta:
        ordering = ['-timestamp_created']
        verbose_name = _('domain')
        verbose_name_gen = pgettext_lazy('genetive singular', 'domain')
        verbose_name_plural = _('domains')
        verbose_name_plural_gen = pgettext_lazy('genetive plural', 'domains')

    def __str__(self):
        return '{0}'.format(self.name)

    def get_absolute_url(self):
        return reverse('altlink:domain-www-detail', kwargs={'slug_dw': self.slug})

    @property
    def summary(self):
        return self.contentowner.content_summary.latest('timestamp_created')


# TO DOlater - UrlBase def Vote Score liczenie powinno override i powinien być tylko i aż średnią ważoną z użyteczności (usefullness) danego linku w każdy z UrlArticleInfo. Czyli jeżeli link jest nie przydatny w 10 artykułach (np vote_score jest poniżej przynajmniej -10pkt w kazdym) a w 1szt UrlArticleInfo jest przydatny i np vote_score jest dodatni conajmniej 10pkt to UrlBase "usefulness" = 10*(-1) + 1*(1) = -9
# TO DO - tag in UrlBase should be auto generated - all tags from UrlArticleInfo connected to this UrlBase
# TO DOmaintenance - when adding slug again, the method pre_save_slug_norm_receiver must be edited as well, and uncomment/add "@receiver(pre_save,sender=UrlBase)" 
class UrlBase(CounterVotesScoreEnteriesMixin, WatchableMixin):
    slug = models.SlugField(editable=False, blank=False, max_length=SETTING_TITLE_SLUG_FIELD_MAX_LENGHT, unique=True)
    url = models.CharField(max_length=SETTING_URL_FIELD_MAX_LENGHT)
    domain_www = models.ForeignKey(DomainWww, on_delete=models.SET_NULL, null=True,  related_name='url_base')
    flag = models.ManyToManyField(Flag, blank=True)
    timestamp_created = models.DateTimeField('date created', auto_now_add=True)
    tag = models.ManyToManyField(Tag, blank=True, editable=False)

    watchlist_users = models.ManyToManyField(settings.AUTH_USER_MODEL, through='WatchlistUrlBase', related_name='watchlist_url_base')

    times_exists_in_alter_articles = models.PositiveIntegerField(default=0, editable=False)

    class Meta:
        ordering = ['-timestamp_created']
        verbose_name = _('base URL')
        verbose_name_gen = pgettext_lazy('genetive', 'base URL')
        verbose_name_plural = _('base URLs')
        verbose_name_plural_gen = pgettext_lazy('genetive plural', 'base URLs')

    def get_absolute_url(self):
        return reverse('altlink:url-base-detail', kwargs={'slug_ub': self.slug})

class WatchlistUrlBase(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    url_base = models.ForeignKey('UrlBase', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'url_base')

    def __str__(self):
        return ('{0} {1} {2}'.format( self.user.username, _('saved'), self.url_base ))

# TO DOafterdev - decide if ImageField have to have erased blank=True, null=True after dev time - maybe not all AlterArticles should have Images? Maybe Images can be auto-generated from title - only text in image to always have an image
class AlterArticle(CounterVotesScoreEnteriesMixin, WatchableMixin, CreatorCanDeleteUpdateMixin, CommentableMixin):
    slug = models.SlugField(editable=False, blank=False, max_length=SETTING_TITLE_SLUG_FIELD_MAX_LENGHT)
    image_url = models.URLField(
        max_length=SETTING_URL_FIELD_MAX_LENGHT,
        # default='',
        # blank=True,
        # null=True
    )
    image_file = models.ImageField(
        upload_to='images/alter_article/%Y/%m/%d/',
        blank=True,
        null=True
    )
    category_article = models.ManyToManyField(CategoryArticle)
    timestamp_created = models.DateTimeField('date created', auto_now_add=True)
    flag = models.ManyToManyField(Flag, blank=True)
    tag = models.ManyToManyField(Tag, blank=True)

    watchlist_users = models.ManyToManyField(settings.AUTH_USER_MODEL, through='WatchlistAlterArticle', related_name='watchlist_alter_article')

    # timestamp aka 'date modified' is harder to write, because it has to be changed 
    # not only when AlterArticle model will be changed but also when ContentTitle,Summary etc is changing
    # so maybe it isn't so needed right now 
    # timestamp = models.DateTimeField('date modified', auto_now=True)

    # user name should be max_leng`th=21:27
    # USER model update to store info from wich IP user logged in with timestamp - STATISTICS for when and where users are login/voting/etc to sort by timestamp 
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET(get_sentinel_user)) # creator of the AlterArticle

    # VOTES pro/con/alter
    vote_pro_counter = models.PositiveIntegerField(default=0, editable=False)
    vote_con_counter = models.PositiveIntegerField(default=0, editable=False)
    vote_alter_counter = models.PositiveIntegerField(default=0, editable=False)

    # LINKs pro/con/alter
    link_pro_counter = models.PositiveIntegerField(default=0, editable=False)
    link_con_counter = models.PositiveIntegerField(default=0, editable=False)
    link_alter_counter = models.PositiveIntegerField(default=0, editable=False)

    hot_score = models.DecimalField(default=0, max_digits=14, decimal_places=7, null=True, blank=True)
    controversial_score = models.DecimalField(default=0, max_digits=9, decimal_places=8, null=True, blank=True)    # many good comments on PRO and CON type_url so it's not clear verdict
    alternative_score = models.DecimalField(default=0, max_digits=9, decimal_places=8)  # how good are alterlinks in ALTER type_url


    # objects = AlterArticleQuerySet.as_manager()
    objects = AlterArticleManager()

    # TO DOlater - score_pro/con/alter in other way in compare to vote_pro_counter/con/alter - like when one url_article_info has many upvotes (i.e. 1000) so then one upvote more has lee 'power' on score_pro than if somebody will add new link with one upvote. Latter should have more impact on power because is stimulate users to add more interesting links.
    #  # SCORE pro/con/alter
    # score_pro = models.PositiveIntegerField(default=0, editable=False)
    # score_con = models.PositiveIntegerField(default=0, editable=False)
    # score_alter = models.PositiveIntegerField(default=0, editable=False)


    # # VISIBILITY
    # # status of article, sum is different for each combination (i.e visibility in numbers),
    # # next group should be value +10 then sum of each before - 0+40+80= 120 - article STATUS i.e. visibility to users admins, premium,category
    # # even it's CharField, it can store combination of number and chars i.e. 
    # # "160,draft,hidden,etc"
    # VISIBILE_ADMINS = 0
    # VISIBILE_MODS = 10
    # VISIBILE_MODS_CATEGORY = 20
    # VISIBILE_USERS_PREMIUM = 40
    # VISIBILE_USERS_CATEGORY = 80
    # VISIBILE_USERS_ALL = 160
    # status = models.CharField(max_length=20)
    
    # # like 'status' but for comments for visibility of comments
    # # if they are 'on' or 'off'
    # status_comment = models.CharField(max_length=20)


    # FIELDS TO THINK OF:

    # URL links to other URLs, so two of those links are telling something else / or telling the same

    # przapadki (cases) in english http://www.popolskupopolsce.edu.pl/pogotowie-jezykowe
    class Meta:
        ordering = ['-timestamp_created']
        verbose_name = _('AlterArticle')
        verbose_name_gen = pgettext_lazy('genetive singular', 'AlterArticle')
        verbose_name_plural = _('AlterArticles')
        verbose_name_plural_gen = pgettext_lazy('genetive plural', 'AlterArticles')

    def __str__(self):
        return '{0}: {1}'.format(self._meta.verbose_name.title(), self.title)

    def get_absolute_url(self):
        return reverse('altlink:alter-article-detail', kwargs={'slug_aa': self.slug})
    
    @property
    def get_absolute_url_edit(self):
        return reverse('altlink:alter-article-update', kwargs={'slug_aa': self.slug})

    @property
    def get_absolute_url_delete(self):
        return reverse('altlink:alter-article-delete', kwargs={'slug_aa': self.slug})

    def update_all_scores(self):
        self.update_hot_score()
        self.update_best_score()
        self.update_alternative_score()
        self.update_controversial_score()
        self.update_rest_scores()


    def links_good_best_score_proconalter_sum(self, type_url, best_score_min=SETTING_ALTERLINK_GOOD_BEST_SCORE_MINIMAL_VALUE_SUM_SCORE):
        """
        returns sum of good alterlinks best scores in alterarticle
        """
        links_good_best_score_sum = self.url_article_info.aggregate( links_good_best_score_sum=Coalesce(Sum('best_score', filter=(Q(type_url=type_url) & Q(best_score__gte=best_score_min))), V(0)) )['links_good_best_score_sum']
        return links_good_best_score_sum
    
    def links_good_proconalter_count(self, type_url, best_score_min=SETTING_ALTERLINK_GOOD_BEST_SCORE_MINIMAL_VALUE_MAIN):
        """
        returns number of good alterlinks in alterArticle (good mean best_score is greater than provided CONSTANS)
        """
        links_good_count = self.url_article_info.aggregate( links_best_score_count=Coalesce(Count('type_url', filter=(Q(type_url=type_url) & Q(best_score__gte=best_score_min))), V(0)) )['links_best_score_count']
        return links_good_count

    def update_hot_score(self):
        """
        hot score based on this formula https://docs.google.com/spreadsheets/d/1BQzDvN_6Fm112BeaYIYm3NgnkLYwnVZGrrzVBpfEQog/edit#gid=615431112&range=M4 (mmwielgosz)
        and https://drive.google.com/file/d/1O4HBSBaMP-ASy74Wevs71KNSosqTg2C6/view?usp=sharing https://drive.google.com/file/d/1O4NTjhY6nUi43LAyQl1sHNp2tNWQedS7/view?usp=sharing
        """
        time_denominator = 86400    # days in seconds (1day = 86400seconds)
        timeframe_promote = 259200    # days in seconds (1day = 86400seconds)

        time_only_factor_fixed = date_seconds_from_fixed_start(self.timestamp_created)/time_denominator

        links_good_all = self.links_good_proconalter_count('pro') + self.links_good_proconalter_count('con') + self.links_good_proconalter_count('alter')
        if links_good_all == 0: #cannot be no good links because below formula of voteup_with_links_good would be ZERO even if there would be many positive vote_up
            links_good_all = 1
        voteup_with_links_good = (self.vote_up_counter + links_good_all )*log((10*links_good_all),10)
        if voteup_with_links_good >= self.vote_down_counter:
            main_hot_factor = self.best_score_weightning_confidance(voteup_with_links_good,self.vote_down_counter)
        else:
            x = self.best_score_weightning_confidance(self.vote_down_counter, voteup_with_links_good)   # switched vote_down and vote_up because we want to know how confident are votes_down
            if x>= 0.999999:
                x=0.999999  # preserve that not divide by ZERO in below main_hot_factor formula
            main_hot_factor = 1.0/((x**0.8)-1.0)   # '-1.0' because it should be substracted from time_only_factor_fixed because when there is more vote_down it should lower 'hotness' of hot_score

        vote_timeframe_promote_factor = main_hot_factor * timeframe_promote/time_denominator

        self.hot_score = time_only_factor_fixed + vote_timeframe_promote_factor

        self.save()

    def update_vote_proconalter_counter(self, type_url_passed):
        vote_proconalter_counter_updated = (
            self.url_article_info.aggregate( votes_sum=Coalesce( Sum('vote_score', filter=(Q(type_url=type_url_passed) & Q(vote_score__gte=0))), V(0) ) )
            )['votes_sum']

        # pro/con/alter not negative - UrlArticleInfo only can add good votes to either pro link or con link or alter link. If pro/con/alter link has negative vote_score then it only means that 
        # it has no value to pro/con/alter voting which it is now and should be recognized as meant to moved to 
        # other pro/con/alter (sa type_url should be considered to be changed) or to be marked as 'untrusted source' or deleted. Should be 
        # automatictly flagged as 'move to other type url' or to marked as "untrusted source" or to be deleted is i.e. 30% of votes are votedown.
        if vote_proconalter_counter_updated <= 0:
            vote_proconalter_counter_updated = 0
        if type_url_passed=='pro':
            self.vote_pro_counter = vote_proconalter_counter_updated
        if type_url_passed=='con':
            self.vote_con_counter = vote_proconalter_counter_updated
        if type_url_passed=='alter':
            self.vote_alter_counter = vote_proconalter_counter_updated
        self.save()

    # update link type url counters but only when vote_score for particular AlterLink is not below zero (considered bad link to delete or move to another type_url)
    def update_links_proconalter_counter(self, type_url_passed):
        link_proconalter_counter_updated = (
            self.url_article_info.aggregate( links_sum=Coalesce( Count('type_url', filter=Q(type_url=type_url_passed) & Q(vote_score__gte=0)), V(0) ) )
            )['links_sum']

        # pro/con/alter not negative - UrlArticleInfo only can add good votes to either pro link or con link or alter link. If pro/con/alter link has negative vote_score then it only means that 
        # it has no value to pro/con/alter voting which it is now and should be recognized as meant to moved to 
        # other pro/con/alter (sa type_url should be considered to be changed) or to be marked as 'untrusted source' or deleted. Should be 
        # automatictly flagged as 'move to other type url' or to marked as "untrusted source" or to be deleted is i.e. 30% of votes are votedown.
        if link_proconalter_counter_updated <= 0:
            link_proconalter_counter_updated = 0
        if type_url_passed=='pro':
            self.link_pro_counter = link_proconalter_counter_updated
        if type_url_passed=='con':
            self.link_con_counter = link_proconalter_counter_updated
        if type_url_passed=='alter':
            self.link_alter_counter = link_proconalter_counter_updated
        self.save()

    def update_controversial_score(self):
        """
        main part of controversial_score values from 0..1. (where 1.0 is max). BUT then this main part is multiplied by power_of_votes_number. 
        So when more votes then main_controversy_factor (0..1) will raise up controversy factor
        AlterLinks counted to controvercial scores must have their best_score at least of value SETTING_ALTERLINK_GOOD_BEST_SCORE_MINIMAL_VALUE_MAIN
        """
        links_good_pro = self.links_good_best_score_proconalter_sum(type_url='pro')
        links_good_con = self.links_good_best_score_proconalter_sum(type_url='con')
        if links_good_pro != 0 or links_good_con != 0:
            power_of_votes_number = links_good_pro + links_good_con
            main_controversy_factor = float(1.0)-(abs(float(links_good_pro) - float(links_good_con)) / (float(links_good_pro) + float(links_good_con)))
            self.controversial_score = float(main_controversy_factor) * float(power_of_votes_number)
        else:
            self.controversial_score = 0
        self.save()

    def update_alternative_score(self):
        """
        alternative_score values is count of good AlterLinks with type_url = 'alter'
        AlterLinks counted to alternative score must have their best_score at least of value SETTING_ALTERLINK_GOOD_BEST_SCORE_MINIMAL_VALUE_SUM_SCORE
        """
        best_score_alter = self.links_good_best_score_proconalter_sum(type_url='alter')
        if best_score_alter > 0:
            self.alternative_score = best_score_alter
        else:
            self.alternative_score = 0
        self.save()

    def progressbar_calculate_per_counter(self, vote_counter_chosen):
        result = 0
        if self.vote_pro_counter==0 and self.vote_con_counter==0 and self.vote_alter_counter==0:
            result = 0
        else:
            result = vote_counter_chosen/(self.vote_pro_counter + self.vote_con_counter + self.vote_alter_counter) *100
        return result

    @property
    def title(self):
        return self.contentowner.content_title.latest('timestamp_created')

    @property
    def excerpt(self):
        return self.contentowner.content_excerpt.latest('timestamp_created')

    @property
    def summary(self):
        return self.contentowner.content_summary.latest('timestamp_created')

    @property
    def progressbar_pro(self):
        return self.progressbar_calculate_per_counter(self.vote_pro_counter)
    
    @property
    def progressbar_con(self):
        return self.progressbar_calculate_per_counter(self.vote_con_counter)
    
    @property
    def progressbar_alter(self):
        return self.progressbar_calculate_per_counter(self.vote_alter_counter)

class WatchlistAlterArticle(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    alter_article = models.ForeignKey('AlterArticle', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'alter_article')

    def __str__(self):
        return ('{0} {1} {2}'.format( self.user.username, _('saved'), self.alter_article ))


# class UrlArticleInfoManager(model.Manager):
#     def filter_by_type_url(self,instance):

#         return   

# TO DOlater - slug field generate. Can be sulg of alterArticle + 
# maybe slug from URLfield? or title of URL site
class UrlArticleInfo(CounterVotesScoreEnteriesMixin, WatchableMixin, CreatorCanDeleteUpdateMixin, CommentableMixin):
    CHOICES_TYPE_URL = [
        ('pro', 'Pro'),
        ('con', 'Con'),
        ('alter', 'Alternative'),
    ]

    slug = models.SlugField(editable=False, blank=False, max_length=SETTING_TITLE_SLUG_FIELD_MAX_LENGHT, unique=True)
    type_url = models.CharField(verbose_name=_('URL type'), max_length=10, choices=CHOICES_TYPE_URL)  # which type this url is for this AlterArticle: pro, con, alter
    alter_article = models.ForeignKey(AlterArticle, on_delete=models.CASCADE, related_name='url_article_info')
    url_base = models.ForeignKey(UrlBase, on_delete=models.CASCADE, related_name='url_article_info')
    # text_excerpt = models.TextField(blank=True,default='',help_text=_('Interesting fragment of the text from above URL where other users should start reading or read all - paste it here so link will point directly to this fragment.'))
    flag = models.ManyToManyField(Flag, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET(get_sentinel_user))
    timestamp_created = models.DateTimeField('date created', auto_now_add=True)
    
    # maybe all TAGs from UrlArticleInfo are the same like TAGs in AlterArticle, or at least should be the same, so we don't need TAGs in UrlArticleInfo
    tag = models.ManyToManyField(Tag, blank=True)

    watchlist_users = models.ManyToManyField(settings.AUTH_USER_MODEL, through='WatchlistUrlArticleInfo', related_name='watchlist_url_article_info')

    class Meta:
        ordering = ['-timestamp_created']
        verbose_name = _('AlterLink')
        verbose_name_gen = pgettext_lazy('genetive', 'AlterLink')
        verbose_name_plural = _('AlterLinks')
        verbose_name_plural_gen = pgettext_lazy('genetive plural', 'AlterLinks')

    def __str__(self):
        return '{0}: {1}'.format(self._meta.verbose_name.title(), self.url)

    def save(self, *args, **kwargs):
        qs_count_url_base = UrlArticleInfo.objects.filter(url_base=self.url_base).count()
        if qs_count_url_base > self.url_base.times_exists_in_alter_articles: # check / update how many times this particular UrlBase exists in database. In how many AlterArticles was used
            self.url_base.times_exists_in_alter_articles = qs_count_url_base
            self.url_base.save()

        qs_count_domain_www = UrlArticleInfo.objects.filter(url_base__domain_www=self.url_base.domain_www).count()
        if qs_count_domain_www > self.url_base.domain_www.times_exists_in_alter_articles: # check / update how many times this particular UrlBase exists in database. In how many AlterArticles was used
            self.url_base.domain_www.times_exists_in_alter_articles = qs_count_domain_www
            self.url_base.domain_www.save()

        super(UrlArticleInfo, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if UrlArticleInfo.objects.filter(url_base=self.url_base).count() < 2: # so there is only one instance of UrlAlterInfo with relation to UrlBase, so we can delete this instance of UrlBase 
            self.url_base.delete()
        super(UrlArticleInfo, self).delete(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('altlink:url-article-info-detail', kwargs={'pk_aa': self.alter_article.pk, 'slug_uai': self.slug})

    @property
    def get_absolute_url_edit(self):
        return reverse('altlink:url-article-info-update', kwargs={'pk_aa': self.alter_article.pk, 'slug_uai': self.slug})

    @property
    def get_absolute_url_delete(self):
        return reverse('altlink:url-article-info-delete', kwargs={'pk_aa': self.alter_article.pk, 'slug_uai': self.slug})

    @property
    def summary(self):
        return self.contentowner.content_summary.latest('timestamp_created')

    @property
    def quotation_best(self):
        """
        checking if there is quotation for provided AlterLink. if IS -> then return best quotation. If NOT -> return empty string
        """
        qs = ''
        qs_check = False
        try:
            qs_check = self.contentowner.content_quotation.order_by('-vote_score', '-timestamp_created').first()
        except ContentQuotation.DoesNotExist as error:
            pass
            # logger.info( error )
        
        if qs_check:
            qs = qs_check
        return qs

    @property
    def quotation_best_text_marked(self):
        return str( "\"" + self.quotation_best.text + "\"")

    @property
    def url(self):
        return self.url_base.url

    @property
    def url_quotation_best(self):
        url_ = self.url_base.url
        if str(self.quotation_best) != '' and self.quotation_best != None:
            url_ = url_ + '#:~:text=' + str(self.quotation_best.text)
        return url_
        
class WatchlistUrlArticleInfo(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    url_article_info = models.ForeignKey('UrlArticleInfo', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'url_article_info')

    def __str__(self):
        return ('{0} {1} {2}'.format( self.user.username, _('saved'), self.url_article_info ))



# REST SMALL MODELS
#


# TO DOmaintenance - When adding a model that will have 
# history of 'title', 'summary' etc. It must be also added 
# to this below '@property' 
class OwnerMixin(models.Model):
    """
    in general Owners approach was decide and based on
    https://bitbucket.org/spookylukey/djangoadmintips/src/default/generic_foreign_key_tests/alternative2/models.py
    https://lukeplant.me.uk/blog/posts/avoid-django-genericforeignkey/ alternative 2 content owner genericforeignkey
    """
    # content_type_model = ''
    # def __init__(self, *args, **kwargs):
    #     self.content_type_model = kwargs.get('ctm', '')
    #     super(OwnerMixin, self).__init__()
    # related_name_custom = '{0}content_owner'.format(content_type_model)
    domain_www = models.OneToOneField(DomainWww, null=True, blank=True, on_delete=models.CASCADE)
    alter_article = models.OneToOneField(AlterArticle, null=True, blank=True, on_delete=models.CASCADE)
    url_article_info = models.OneToOneField(UrlArticleInfo, null=True, blank=True, on_delete=models.CASCADE)
    # TO DOlater - mayhbe url_base don't have to be here because it doesn't have any Content inside for now
    # url_base = models.OneToOneField(UrlBase, null=True, blank=True, on_delete=models.CASCADE)

    class Meta:
        abstract = True

    # TO DOmaintenance - for each field in ContentOwner there has to be equivalent in 'target' method
    @property
    def target(self):
        if self.domain_www is not None:
            return self.domain_www
        if self.alter_article is not None:
            return self.alter_article
        if self.url_article_info is not None:
            return self.url_article_info
        # if self.url_base is not None:
        #     return self.url_base
        raise AssertionError('There is no ContentOwner in this instance - pk: {0}'.format(self.pk))


class StatusOwner(OwnerMixin):
    pass

# TO DOlater - think of more status values
class Status(models.Model):
    CHOICES_STATUS_VALUE = [
        (None, 'None'),
        ('only_admins_see', 'AlterArticle visible only for admins'),  # in case of making article dissapear from alter-link.com but not from database
        ('wait_for_approval', 'AlterArticle suspended till verification'),  # possibility of breaking rules of alter-link.com

        # (None, 'Brak'),
        # ('only_admins_see', 'Artykuł widoczny tylko dla administratorów'),  # in case of making article dissapear from alter-link.com but not from database
        # ('wait_for_approval', 'Artykuł wstrzymany do akceptacji'),  # possibility of breaking rules of alter-link.com
    ]
    value = models.CharField(max_length=30, choices=CHOICES_STATUS_VALUE, null=True, blank=True, default=None)
    status_owner = models.OneToOneField(StatusOwner, on_delete=models.CASCADE)  # each status is only one to one StatusOwner (one AlterArticle has one status, one DomainWww has one status etc.) 
    timestamp_created = models.DateTimeField('date created', auto_now_add=True)

    class Meta:
        ordering = ['-timestamp_created']


# CONTENTS
#

# Parent class - Content for all subContent classes that are below
class Content(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET(get_sentinel_user))
    timestamp_created = models.DateTimeField('date created', auto_now_add=True)
    flag = models.ManyToManyField(Flag, blank=True)

    class Meta:
        # to create in database table "Content"
        # "abstract=True" - class "Content" is only for inheritance of ContentText, Content CharLong etc.
        abstract=True
        ordering = ['-timestamp_created']


class ContentOwner(OwnerMixin):
    pass
    # """
    # in general Owners approach was decide and based on
    # https://bitbucket.org/spookylukey/djangoadmintips/src/default/generic_foreign_key_tests/alternative2/models.py
    # """
    # domain_www = models.OneToOneField(DomainWww, null=True, blank=True, on_delete=models.CASCADE, related_name='contentowner')
    # alter_article = models.OneToOneField(AlterArticle, null=True, blank=True, on_delete=models.CASCADE, related_name='contentowner')
    # url_article_info = models.ForeignKey(UrlArticleInfo, null=True, blank=True, on_delete=models.CASCADE, related_name='contentowner')
    # url_base = models.ForeignKey(UrlBase, null=True, blank=True, on_delete=models.CASCADE, related_name='contentowner')

    # # TO DOmaintenance - for each field in ContentOwner there has to be equivalent in 'target' method
    # @property
    # def target(self):
    #     if self.domain_www is not None:
    #         return self.domain_www
    #     if self.alter_article is not None:
    #         return self.alter_article
    #     if self.url_article_info is not None:
    #         return self.url_article_info
    #     if self.url_base is not None:
    #         return self.url_base
    #     raise AssertionError('There is no ContentOwner in this instance - pk: {0}'.format(self.pk))


def str_method_for_content_models(model_instance):
    """
    simple easy just to rememeber how to make 'global' __str__ methods
    """
    try:
        # text = model_instance._meta.verbose_name_gen + ': ' + model_instance.text
        text = model_instance.text
    except ObjectDoesNotExist:
        text = None
    return text


class ContentSummary(Content, CounterVotesScoreEnteriesMixin, CreatorCanDeleteUpdateMixin, CommentableMixin):
    text = models.TextField(max_length = SETTING_SUMMARY_FIELD_MAX_LENGHT, blank=True, default='')
    contentowner = models.ForeignKey(ContentOwner, on_delete=models.CASCADE, related_name="content_summary")

    class Meta:
        ordering = ['-vote_score','-timestamp_created']
        verbose_name = _('Summary')
        verbose_name_gen = pgettext_lazy('genetive', 'Summary')
        verbose_name_plural = _('Summaries')
        verbose_name_plural_gen = pgettext_lazy('genetive plural', 'Summaries')

    def __str__(self):
        return str_method_for_content_models(self)

    # TODO #11
    @property
    def get_absolute_url_edit(self):
        if self.contentowner.target.__class__.__name__ == 'AlterArticle':
            return reverse('altlink:content-summary-aa-update', kwargs={'pk_aa': self.contentowner.target.pk, 'pk_cs': self.pk})
        if self.contentowner.target.__class__.__name__ == 'UrlArticleInfo':
            return reverse('altlink:content-summary-uai-update', kwargs={'pk_aa': self.contentowner.target.alter_article.pk, 'slug_uai': self.contentowner.target.slug, 'pk_cs': self.pk})

    @property
    def get_absolute_url_delete(self):
        if self.contentowner.target.__class__.__name__ == 'AlterArticle':
            return reverse('altlink:content-summary-aa-delete', kwargs={'pk_aa': self.contentowner.target.pk, 'pk_cs': self.pk})
        if self.contentowner.target.__class__.__name__ == 'UrlArticleInfo':
            return reverse('altlink:content-summary-uai-delete', kwargs={'pk_aa': self.contentowner.target.alter_article.pk, 'slug_uai': self.contentowner.target.slug, 'pk_cs': self.pk})

class ContentExcerpt(Content):
    text = models.CharField(max_length=SETTING_EXCERPT_FIELD_MAX_LENGHT, blank=True, default='')
    contentowner = models.ForeignKey(ContentOwner, on_delete=models.CASCADE, related_name="content_excerpt")

    class Meta:
        ordering = ['-timestamp_created']
        verbose_name = _('Excerpt')
        verbose_name_gen = pgettext_lazy('genetive', 'Excerpt')
        verbose_name_plural = _('Excerpts')
        verbose_name_plural_gen = pgettext_lazy('genetive plural', 'Excerpts')

    def __str__(self):
        return str_method_for_content_models(self)

class ContentTitle(Content, CreatorCanDeleteUpdateMixin):
    text = models.CharField(max_length=SETTING_TITLE_SLUG_FIELD_MAX_LENGHT, default='')
    contentowner = models.ForeignKey(ContentOwner, on_delete=models.CASCADE, related_name="content_title")

    class Meta:
        ordering = ['-timestamp_created']
        verbose_name = _('Title')
        verbose_name_gen = pgettext_lazy('genetive', 'Title')
        verbose_name_plural = _('Titles')
        verbose_name_plural_gen = pgettext_lazy('genetive plural', 'Titles')

    def __str__(self):
        return str_method_for_content_models(self)

class ContentQuotation(Content, CounterVotesScoreEnteriesMixin, CreatorCanDeleteUpdateMixin, CommentableMixin):
    text = models.CharField(max_length=SETTING_QUOTATION_FIELD_MAX_LENGHT, blank=True, default='')
    contentowner = models.ForeignKey(ContentOwner, on_delete=models.CASCADE, related_name="content_quotation")

    class Meta:
        ordering = ['-vote_score','-timestamp_created']
        verbose_name = _('Quotation')
        verbose_name_gen = pgettext_lazy('genetive', 'Quotation')
        verbose_name_plural = _('Quotations')
        verbose_name_plural_gen = pgettext_lazy('genetive plural', 'Quotations')

    def __str__(self):
        return str_method_for_content_models(self)

    # TODO #10
    @property
    def get_absolute_url_edit(self):
        if self.contentowner.target.__class__.__name__ == 'UrlArticleInfo':
            return reverse('altlink:content-quotation-uai-update', kwargs={'pk_aa': self.contentowner.target.alter_article.pk, 'slug_uai': self.contentowner.target.slug, 'pk_cq': self.pk})
        
    @property
    def get_absolute_url_delete(self):
        if self.contentowner.target.__class__.__name__ == 'UrlArticleInfo':
            return reverse('altlink:content-quotation-uai-delete', kwargs={'pk_aa': self.contentowner.target.alter_article.pk, 'slug_uai': self.contentowner.target.slug, 'pk_cq': self.pk})

    @property
    def text_quotation(self):
        return str( "\"" + self.text + "\"")

    @property
    def url_quotation(self):
        url_ = self.contentowner.target.url_base.url
        if str(self.text) != '' and self.text != None:
            url_ = url_ + '#:~:text=' + str(self.text)
        return url_


class CommentOwnerMixin(models.Model):
    """
    in general Owners approach was decide and based on
    https://bitbucket.org/spookylukey/djangoadmintips/src/default/generic_foreign_key_tests/alternative2/models.py
    """
    domain_www = models.OneToOneField(DomainWww, null=True, blank=True, on_delete=models.CASCADE)
    alter_article = models.OneToOneField(AlterArticle, null=True, blank=True, on_delete=models.CASCADE)
    url_article_info = models.OneToOneField(UrlArticleInfo, null=True, blank=True, on_delete=models.CASCADE)
    content_summary = models.OneToOneField(ContentSummary, null=True, blank=True, on_delete=models.CASCADE)
    content_quotation = models.OneToOneField(ContentQuotation, null=True, blank=True, on_delete=models.CASCADE)

    class Meta:
        abstract = True

    # TO DOmaintenance - for each field in CommentOwner there has to be equivalent in 'target' method
    @property
    def target(self):
        if self.domain_www is not None:
            return self.domain_www
        if self.alter_article is not None:
            return self.alter_article
        if self.url_article_info is not None:
            return self.url_article_info
        if self.content_summary is not None:
            return self.content_summary
        if self.content_quotation is not None:
            return self.content_quotation
        raise AssertionError ('There is no CommentOwner in this instance - pk: {0}'.format(self.pk))

    def target_field_assign_obj_from_class_name(self, obj=None):
        """
        assiging provided object instance to coresponding field of self object
        target_field_assign_obj_from_class_name is doing self.save() at the end so no need to do this after calling function

        """
        if obj != None:
            class_to_comment = obj.__class__.__name__
            if class_to_comment == DomainWww.__name__:
                self.domain_www = obj
            elif class_to_comment == AlterArticle.__name__:
                self.alter_article = obj
            elif class_to_comment == UrlArticleInfo.__name__:
                self.url_article_info = obj
            elif class_to_comment == ContentSummary.__name__:
                self.content_summary = obj
            elif class_to_comment == ContentQuotation.__name__:
                self.content_quotation = obj
            else:
                AttributeError("In method 'target_field_assign_obj_from_class_name' 'class_to_comment' was not commentable. Obj: {0}. Class to comment: {1}.".format(obj, obj.__class__.__name__) )
            self.save()
            return self
            
        else:
            raise AttributeError("In method 'target_field_assign_obj_from_class_name' there wasn't provided 'obj'. Obj: {0}.".format(obj) )

class ContentOwnerComment(CommentOwnerMixin):
    pass

# TO DO - check all comment is it good
# TO DO - status? CharField(20)
class ContentComment(Content, CreatorCanDeleteUpdateMixin, WatchableMixin, CounterVotesScoreEnteriesMixin):
    """
    To create a recursive relationship – an object that has a 
    many-to-one relationship with itself – use 
    models.ForeignKey('self', on_delete=models.CASCADE).
    """
    id = models.BigAutoField(primary_key=True)
    text = models.TextField()
    contentownercomment = models.ForeignKey(ContentOwnerComment, on_delete=models.CASCADE, related_name='content_comment')

    is_edited = models.BooleanField(default=False)
    parent_comment = models.ForeignKey('self', on_delete=models.CASCADE, related_name='children', null=True, blank=True)

    watchlist_users = models.ManyToManyField(settings.AUTH_USER_MODEL, through='WatchlistContentComment', related_name='watchlist_content_comment')

    class Meta:
        ordering = ['-timestamp_created']
        verbose_name = _('Comment')
        verbose_name_gen = pgettext_lazy('genetive', 'Comment')
        verbose_name_plural = _('Comments')
        verbose_name_plural_gen = pgettext_lazy('genetive plural', 'Comments')

    def __str__(self):
        if self.is_edited:
            return self.edits.latest('timestamp_created').text
        else:
            return self.text
    
    @property
    def last_edit(self):
        if self.is_edited:
            return self.edits.latest('timestamp_created')
        else:
            return self.text

    @property
    def comment_children(self):
        """
        return all children of the comment in order_by('-timestamp_created')
        """
        return self.children.all().order_by('-timestamp_created')

class ContentCommentEdit(models.Model):
    id = models.BigAutoField(primary_key=True)
    timestamp_created = models.DateTimeField('date created', auto_now_add=True)
    text = models.TextField()
    original_comment = models.ForeignKey('ContentComment', on_delete=models.CASCADE, related_name='edits', null=True, blank=True)

    class Meta:
        ordering = ['-timestamp_created']
        verbose_name = _('Comment')
        verbose_name_gen = pgettext_lazy('genetive', 'Comment')
        verbose_name_plural = _('Comments')
        verbose_name_plural_gen = pgettext_lazy('genetive plural', 'Comments')

    def __str__(self):
        return self.text

class WatchlistContentComment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content_comment = models.ForeignKey('ContentComment', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'content_comment')
        verbose_name = _('Comment')
        verbose_name_gen = pgettext_lazy('genetive', 'Comment')
        verbose_name_plural = _('Comments')
        verbose_name_plural_gen = pgettext_lazy('genetive plural', 'Comments')

    def __str__(self):
        return ('{0} {1} {2}'.format( self.user.username, _('saved'), self.content_comment ))

# VOTES
#

class Vote(models.Model):
    id = models.BigAutoField(primary_key=True)
    value = models.SmallIntegerField(default=1)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET(get_sentinel_user))
    timestamp_created = models.DateTimeField('date created', auto_now_add=True)
    timestamp = models.DateTimeField('date modified', auto_now=True)

    class Meta:
        abstract = True
        ordering = ['-timestamp_created']
        verbose_name = _('Vote')
        verbose_name_gen = pgettext_lazy('genetive', 'Vote')
        verbose_name_plural = _('Votes')
        verbose_name_plural_gen = pgettext_lazy('genetive plural', 'Votes')

    def __str__(self):
        return "Vote: {0}, by user: {1}, date: {2}".format(self.value, self.user, self.timestamp)

class VoteAlterArticle(Vote):
    alter_article = models.ForeignKey(AlterArticle, on_delete=models.CASCADE, related_name='votes')

class VoteDomainWww(Vote):
    domain_www = models.ForeignKey(DomainWww, on_delete=models.CASCADE, related_name='votes')

class VoteComment(Vote):
    comment = models.ForeignKey(ContentComment, on_delete=models.CASCADE, related_name='votes')

class VoteUrlBase(Vote):
    url_base = models.ForeignKey(UrlBase, on_delete=models.CASCADE, related_name='votes')

class VoteUrlArticleInfo(Vote):
    url_article_info = models.ForeignKey(UrlArticleInfo, on_delete=models.CASCADE, related_name='votes')

class VoteQuotation(Vote):
    content_quotation = models.ForeignKey(ContentQuotation, on_delete=models.CASCADE, related_name='votes')

class VoteSummary(Vote):
    content_summary = models.ForeignKey(ContentSummary, on_delete=models.CASCADE, related_name='votes')


# ENTERED
#

# TO DOlater - in future add logs when user it's loggin-in check periodiclly IP and GPS 
# for having table of when user was and where (statistics for searching things and users)
class Entered(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET(get_sentinel_user))
    timestamp_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ['-timestamp_created']
        verbose_name = _('Entry')
        verbose_name_gen = pgettext_lazy('genetive', 'Entry')
        verbose_name_plural = _('Entries')
        verbose_name_plural_gen = pgettext_lazy('genetive plural', 'Entries')

    def __str__(self):
        return 'Entered user: {0}, date: {1}'.format(self.user, self.timestamp_created)

class EnteredAlterArticle(Entered):
    alter_article = models.ForeignKey(AlterArticle, on_delete=models.CASCADE, related_name='enteries')

class EnteredDomainWww(Entered):
    domain_www = models.ForeignKey(DomainWww, on_delete=models.CASCADE, related_name='enteries')

class EnteredUrlArticleInfo(Entered):
    url_article_info = models.ForeignKey(UrlArticleInfo, on_delete=models.CASCADE, related_name='enteries')

class EnteredUrlBase(Entered):
    url_base = models.ForeignKey(UrlBase, on_delete=models.CASCADE, related_name='enteries')


# METHODS
#


### START - PRE save

# TO DOmaintenance - maybe not always method should be lunched when saving ContentTitle?
# maybe not for all ContentTitle there will be computed slug for url making? 
def pre_save_model_receiver(sender, instance, *args, **kwargs):
    """
    making slug from title instance when saving ContentTitle
    """
    if instance.contentowner.target.__class__.__name__ == 'AlterArticle':
        if not instance.contentowner.target.slug:
            instance.contentowner.target.slug = slug_unique_generator_alter_article(instance)
            instance.contentowner.target.has_slug = True
            instance.contentowner.target.save()

# TO DOlater - test slug generating in all models
@receiver(pre_save,sender=UrlBase)
@receiver(pre_save,sender=DomainWww)
@receiver(pre_save,sender=UrlArticleInfo)
def pre_save_slug_norm_receiver(sender, instance, *args, **kwargs):
    """
    making slug from giver args of instance before saving instance
    """
    senders_to_slugify = ['DomainWww', 'UrlArticleInfo']
    if not instance.slug:
        if instance.__class__.__name__ == 'DomainWww':
            # print('netloc: {0}'.format(urlparse(instance.url).netloc))
            instance.slug = slug_unique_generator_args(instance, list_of_slug_args=[ urlparse(instance.url).netloc ] )
        if instance.__class__.__name__ == 'UrlArticleInfo':
            instance.slug = slug_unique_generator_args(instance, list_of_slug_args=[ instance.url_base.slug ] ) # can't be slug with instance.type_ulr because some UrlArticleInfo can be first i.e. "Pro" and then after voting they can be "alter" because community will decide this way
        if instance.__class__.__name__ == 'UrlBase':
            parsed_url_urlparse = urlparse(instance.url)
            instance.slug = slug_unique_generator_args(instance, list_of_slug_args=[ instance.domain_www.slug, parsed_url_urlparse.path ])
        instance.has_slug = True

# !!!
def pre_save_url_base_get_or_create_receiver(sender, instance, *args, **kwargs):
    pass
    # UrlBase.objects.get_or_create(
    #     url = instance.
    # )

pre_save.connect(pre_save_model_receiver, sender=ContentTitle)

pre_save.connect(pre_save_slug_norm_receiver, sender=DomainWww)
pre_save.connect(pre_save_slug_norm_receiver, sender=UrlArticleInfo)
pre_save.connect(pre_save_url_base_get_or_create_receiver, sender=UrlArticleInfo)

### END - PRE save


### START - POST save

@receiver(post_save,sender=UrlArticleInfo)
def post_save_link_counter_update(sender, instance, *args, **kwargs):
    """
    after saving UrlArticleInfo in AlterArticle - need to update link counter in AlterArticle
    """
    instance.alter_article.update_links_proconalter_counter(instance.type_url)
    instance.alter_article.save()


post_save.connect(post_save_link_counter_update, sender=UrlArticleInfo)

### END - POST save
AlterArticle.objects.filter()