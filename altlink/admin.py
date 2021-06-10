from django.contrib import admin

import nested_admin

from .models import (   BannerText, Flag, Tag, AlterArticle, DomainWww, UrlArticleInfo, CategoryArticle, CategoryDomainWww, UrlBase,
                        ContentComment, ContentSummary, ContentExcerpt, ContentTitle, #ContentName, 
                        ContentOwner,ContentOwnerComment,
                        #ContentSummaryOwner, ContentExcerptOwner, ContentTitleOwner, ContentNameOwner
                        BannerText
)

from request.models import (   Request
)

# proxy idea from https://books.agiliq.com/projects/django-admin-cookbook/en/latest/add_model_twice.html
class RequestProxy(Request):

    class Meta:
        proxy = True

# methods for Admin models
#
def content_owner_admin_include_fields(field_that_include):
    """
    method is giving tuple of fields, that we need to exclude from AdminView of model edit/creation
    In example in DomainWww model 'add'/'create' we want to exclude all fields (alter_article, summary, etc) but not 'domain_www'  
    """
    fields_names_list = [f.name for f in ContentOwner._meta.get_fields()]   # list of all fields in Content owner
    while field_that_include in fields_names_list: fields_names_list.remove(field_that_include) # remove field 'field_that_include' f
    return fields_names_list    # field_name_list with updated field list (removed like said in description of methond)


# Admins view Mixins
#
# class UserFillAutoAdminViewMixin(admin.ModelAdmin):
#     def __init__(self, request, *args, **kwargs):
#         if request.user.is_authenticated:
#             super().__init__(*args, **kwargs)
#             self.fields['user'].initial = request.user 


class UserAutoFillAdminMixin(admin.ModelAdmin):

    # exclude = ['user']

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super(UserAutoFillAdminMixin, self).get_form(request, obj, change, **kwargs)
        form.base_fields['user'].initial = request.user
        return form

    # setting up user field in nested inlines to the one which is in AlterArticle initial value
    # https://stackoverflow.com/a/36443466/11423556
    def save_formset(self, request, form, formset, change):
        for form in formset.forms:
            # if hasattr((form.instance), 'user'):
            # form.instance.user=request.user
            if hasattr(form, 'nested_formsets'):
                for content_owner_form in form.nested_formsets:
                    # content_owner_form.instance.user = form.instance.person
                    for content_form in content_owner_form:
                        content_form.instance.user = request.user#form.instance.user2
        super(UserAutoFillAdminMixin, self).save_formset(request, form, formset, change)

    # changing/setting up 'user field' to current logged in 'user' 
    # https://stackoverflow.com/questions/36443245/override-save-method-of-django-admin
    def save_model(self, request, obj, form, change):
        if obj.user:
            obj.user = request.user
        super(UserAutoFillAdminMixin, self).save_model(request, obj, form, change)

    # # https://stackoverflow.com/questions/3016158/django-inlinemodeladmin-set-inline-field-from-request-on-save-set-user-field/3016335
    # def save_formset(self, request, form, formset, change):
    #     # if formset.model != InlineModel:
    #     #     return super(MainModelAdmin, self).save_formset(request, form, formset, change)
    #     instances = formset.save(commit=False)
    #     for instance in instances:
    #         # if not instance.pk:
    #         instance.user = request.user
    #         instance.save()
    #     formset.save_m2m()



# Inlines for minor models
#
class ContentCommentNestedTabularInline(nested_admin.NestedTabularInline):
    model = ContentComment
    exclude = ['user']
    extra = 1
class ContentSummaryNestedTabularInline(nested_admin.NestedTabularInline):
    model = ContentSummary
    exclude = ['user']
    extra = 1
class ContentExcerptNestedTabularInline(nested_admin.NestedTabularInline):
    model = ContentExcerpt
    exclude = ['user']
    extra = 1
class ContentTitleNestedTabularInline(nested_admin.NestedTabularInline):
    model = ContentTitle
    exclude = ['user']
    extra = 1

# class BannerTextNestedTabularInline(nested_admin.NestedTabularInline):
#     model = BannerText
#     exclude = ['user']
#     extra = 1

# class ContentUrlArticleInfoNestedTabularInline(nested_admin.NestedTabularInline):
#     model = UrlArticleInfo
#     exclude = ['user']
#     extra = 1


# class UrlBaseInfoNestedTabularInline(nested_admin.NestedTabularInline):
#     model = UrlBase
#     exclude = ['user']
#     extra = 1


# Inlines for mid models
#
class ContentOwnerDomainWwwNestedTabularInline(nested_admin.NestedTabularInline):
    exclude = content_owner_admin_include_fields('domain_www')
    model = ContentOwner
    inlines = [ContentTitleNestedTabularInline, ContentSummaryNestedTabularInline]
    extra = 1

class ContentOwnerAlterArticleNestedTabularInline(nested_admin.NestedTabularInline):
    # exclude = content_owner_admin_include_fields('alter_article')
    model = ContentOwner
    inlines = [ContentTitleNestedTabularInline, ContentExcerptNestedTabularInline, ContentSummaryNestedTabularInline]
    extra = 1

class ContentOwnerCommentAlterArticleNestedTabularInline(nested_admin.NestedTabularInline):
    exclude = content_owner_admin_include_fields('alter_article')
    model = ContentOwnerComment
    inlines = [ContentCommentNestedTabularInline]
    extra = 1

class ContentOwnerUrlArticleInfoNestedTabularInline(nested_admin.NestedTabularInline):
    exclude = content_owner_admin_include_fields('url_article_info')
    model = ContentOwner
    inlines = [ContentSummaryNestedTabularInline]
    extra = 1

# Admins view
#

# class ContentCommentAdmin(admin.ModelAdmin) 

# ContentSummary, ContentExcerpt, ContentTitle

class DomainWwwAdmin(nested_admin.NestedModelAdmin, UserAutoFillAdminMixin):
    
    inlines = [ContentOwnerDomainWwwNestedTabularInline]

class AlterArticleAdmin(nested_admin.NestedModelAdmin, UserAutoFillAdminMixin):
    
    # inlines = [ContentOwnerAlterArticleNestedTabularInline, ContentOwnerCommentAlterArticleNestedTabularInline]
    inlines = [ContentOwnerAlterArticleNestedTabularInline]

class UrlArticleInfoAdmin(nested_admin.NestedModelAdmin, UserAutoFillAdminMixin):
    
    inlines = [ContentOwnerUrlArticleInfoNestedTabularInline]

# other models
class RequestAdmin(admin.ModelAdmin):
    fields = ('time','path','user','ip','response','method','referer','user_agent','language','is_secure','is_ajax')
    list_display = ('time','path','user','ip','response','method','referer','user_agent','language','is_secure','is_ajax')

class BannerTextAdmin(admin.ModelAdmin):
    pass

# Register your models here.
#

# admin.site.register(ContentOwner)

# admin.site.register(ContentComment)
# admin.site.register(ContentSummary)
# admin.site.register(ContentExcerpt)
# admin.site.register(ContentTitle)

admin.site.register(Flag)
admin.site.register(Tag)
admin.site.register(CategoryArticle)
admin.site.register(CategoryDomainWww)

admin.site.register(UrlArticleInfo, UrlArticleInfoAdmin)
admin.site.register(AlterArticle, AlterArticleAdmin)
admin.site.register(DomainWww, DomainWwwAdmin)

#admin.site.register(ContentName)

admin.site.register(RequestProxy,RequestAdmin)
admin.site.register(BannerText,BannerTextAdmin)