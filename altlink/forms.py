from django import forms

from django.utils.translation import gettext_lazy as _

from django.forms import ModelForm, Textarea, TextInput, URLInput, Select, Form
from .models import AlterArticle, ContentTitle, ContentSummary, ContentExcerpt, ContentQuotation, UrlBase, UrlArticleInfo, DomainWww, ContentComment, Flag, CategoryArticle

from .constans import *

# from .utils import OptionalSchemeURLValidator


class UrlArticleInfoForm(ModelForm):
    
    class Meta:
        model = UrlArticleInfo
        fields = ("type_url",)
        labels = {
            'type_url': _('Link regarding topic of AlterArticle is pro / con / alter?'),
            # 'type_url': _('Link w odniesieniu do AlterArtykułu jest opcją za / przeciw / alter?'),
        }
        widgets = {
            'type_url': Select(attrs={
                'class': 'form-select',
                })
        }

# TO DOlater - possible solution to change empty_label from "---------" to some new label
# https://stackoverflow.com/questions/739260/customize-remove-django-select-box-blank-option/740011#740011
# https://docs.djangoproject.com/en/3.0/ref/forms/fields/#modelchoicefield
# https://stackoverflow.com/questions/54748183/django-modelform-widgets-and-labels
# https://stackoverflow.com/questions/15223506/empty-label-in-widget-select
        # def __init__(self, *args, **kwargs):
        #     super(UrlArticleInfoForm, self).__init__(*args, **kwargs)
        #     self.fields["type_url"].empty_label = 'Is this link pro / con / alter to the topic?'
        #     # following line needed to refresh widget copy of choice list
        #     self.fields["type_url"].widget.choices = self.fields['type_url'].choices


class ContentSummaryUAIForm(ModelForm):
    
    class Meta:
        model = ContentSummary
        fields = ("text",)
        labels = {
            'text': _('Link summary:'),
        }
        widgets = {
            'text': Textarea(attrs={
                'placeholder': _('Please fill this - AlterLink will have more value \nHow this particular link confirms / denies / alters the topic?'),
                'rows':4,
                })
        }


class ContentSummaryDWForm( ModelForm):
    
    class Meta:
        model = ContentSummary
        fields = ("text",)
        labels = {
            'text': _('Domain summary:'),
        }
        widgets = {
            'text': Textarea(attrs={
                'placeholder': _("Please fill this field.\nYou can describe what is main purpose of this domain, is it connected in political manner. You can add link to wikipedia site which describes this domain. Our portal alter-link.com will have more value with this field!"),
                'rows':4,
                })
        }


class AlterArticleForm(ModelForm):

    def clean_category_article(self):
        category_article = self.cleaned_data['category_article']
        if len(category_article) > 3:
            raise forms.ValidationError(_('You can add max 3 categories per AlterArticle'))
        return category_article
    
    class Meta:
        model = AlterArticle
        fields = ('image_url', 'image_file', 'category_article',)
        labels = {
            'image_url': _('Paste direct URL of the picture, which shows well subject of the AlterArticle'),
            'image_file': _('Upload image file, which shows well subject of the AlterArticle'),
            'category_article': _('AlterArticle categories (max&nbsp;3)'),
        }
        widgets = {
            'image_url': URLInput(attrs={
                'placeholder': _('example: https://cdn.pixabay.com/photo/2013/05/20/05/34/alternative-112226_1280.jpg'),
                'rows':1,
                }),
            'category_article': forms.SelectMultiple(attrs={
                'style': 'height: 10em;',
                }),
        }

class ContentTitleAAForm( ModelForm):
    
    class Meta:
        model = ContentTitle
        fields = ("text",)
        labels = {
            'text': _('AlterArticle title:'),
        }
        widgets = {
            'text': TextInput(attrs={'placeholder': _('What topic you would like to discuss or what alternative informations you are searching?')})
        }

class ContentSummaryAAForm( ModelForm):
    
    class Meta:
        model = ContentSummary
        fields = ("text",)
        # REF - changing label of form - https://stackoverflow.com/a/637020/11423556    https://stackoverflow.com/a/28162469/11423556
        labels = {
            'text': _('AlterArticle summary:'),
        }
        widgets = {
            'text': Textarea(attrs={
                'placeholder': _('Please fill this field.\nCan you describe what problem, topic are you raising in this AlterArticle?\nAlterArticle will have more value for our community if you fill this.'),
                'rows':4,
                })
        }

class ContentExcerptAAForm( ModelForm):
    
    class Meta:
        model = ContentExcerpt
        fields = ("text",)
        labels = {
            'text': _('AlterArticle excerpt:'),
        }
        widgets = {
            'text': Textarea(attrs={
                'placeholder': _('If you have time to fill this\nPlease write short, max in 1-2 sentences how to describe subject of this AlterArticle'),
                'rows':3,
                })
        }

class ContentQuotationUAIForm( ModelForm):
    
    class Meta:
        model = ContentQuotation
        fields = ("text",)
        labels = {
            'text': _('Interesting quotation from a link:'),
        }
        widgets = {
            'text': Textarea(attrs={
                'placeholder': _('From provided link paste here interesting quotation or good place to start reading.'),
                'rows':3,
                # 'help_text': _('Interesting fragment of the text from above URL where other users should start reading or read all - paste it here so link will point directly to this fragment.'),
                })
        }

# TO DOlater - if user will paste URL with "https://" or "http://" it should automaticlly add those prefixes and add slashes on the end of URL "/" and then validate
# maybe it will help https://stackoverflow.com/a/30270662/11423556
class UrlBaseForm( ModelForm):
    
    class Meta:
        model = UrlBase
        fields = ("url",)
        labels = {
            'url': _('Link which interest you:'),
        }
        widgets = {
            'url': URLInput(attrs={
                'placeholder': _('Paste here URL, example: https://www.cbc.com/interesting-article'),
                'autofocus': 'autofocus',})
        }

class DomainWwwForm( ModelForm):
    
    class Meta:
        model = DomainWww
        fields = ("name", "url", "category_domain_www", "tag",)
        labels = {
            'name': _('Domain name'),
            'url': _('Domain URL'),
            'category_domain_www': _('Categories that can describe this domain'),
            'tag': _('Tags that can describe this domain'),
        }
        widgets = {
            'url': URLInput(attrs={'placeholder': _('Main domain URL adress, example: https://www.alter-link.com/')}),

            'tag': TextInput(attrs={
                'placeholder': _('example: environmental protection, alternative content, politics, Albert Einstein'),
                'rows':1,
                }),
            'category_domain_www': forms.SelectMultiple(attrs={
                'style': 'height: 10em;',
                }),

        }

class SearchForm(Form):
    q = forms.CharField(
        max_length=2100, 
        required=False, 
        label='', 
        widget=forms.TextInput(
            attrs={
                'placeholder': _('search... with AlterArticle title or paste a link'),
                'autofocus': 'autofocus',
                'style': 'padding: 0.0rem; margin: 0.0rem;',
                'class': 'form-control',
                'aria-label': 'Search',
                'aria-describedby': 'button-navbar_search',
            }
        )
    )

# TODO #12
class WatchlistClassForm(Form):
    CHOICES_CATEGORY_ARTICLE_NAME = [
        (AlterArticle.__name__, AlterArticle._meta.verbose_name_plural),    # with connection to other second categorie like soft,hardware,music,movie to search for an alternative software, food, solution
        (UrlArticleInfo.__name__, UrlArticleInfo._meta.verbose_name_plural),
        # (UrlBase.__name__, UrlBase._meta.verbose_name_plural),
    ]
    class_to_watch = forms.ChoiceField(
        initial={AlterArticle.__name__, AlterArticle._meta.verbose_name_plural},
        label=_('Choose which items list to show:'), 
        choices=CHOICES_CATEGORY_ARTICLE_NAME,
        widget=forms.Select(
            attrs={
                'autofocus': 'autofocus',
                'onchange': 'submit()',
                'class': 'form-select'
            }
        )
    )

class TagAAForm(Form):
    tag = forms.CharField(
        max_length=SETTING_TAG_FORM_FIELD_MAX_LENGHT,
        label=_('AlterArticle hashtags:'),
        required=False,
        widget = forms.Textarea(
            attrs={
                'placeholder': _('example: #environmentalprotection #alternativecontent #politics #alberteinstein'),
                'style': 'height: 5em;',
            }
        )
    )

# class TagUAIForm(TagAAForm):
#     def __init__(self, *args, **kwargs):
#         super(TagUAIForm, self).__init__(*args, **kwargs)
#         self.fields['tag'].label = _('Alterlink hashtags:')

class ContentCommentForm(ModelForm):
    
    class Meta:
        model = ContentComment
        fields = ("text",)
        labels = {
            'text': False,
            # 'text': _('New comment'),
        }
        widgets = {
            'text': Textarea(attrs={
                'placeholder': _("Write your alternative thougths"),
                'rows':2,
                'style': 'font-size: 0.7rem; margin: 0.0rem;',
                })
        }

class FlagForm(ModelForm):
    class Meta:
        model = Flag
        fields = ('name',)
        labels = {
            'name': _('Choose flag'),
        }
        widgets = {
            'name': forms.Select(),
        }
