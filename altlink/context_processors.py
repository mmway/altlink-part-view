# from django.contrib.sites.models import Site

# idea from https://stackoverflow.com/a/24352874
def base_context_processor(request):
    #  return {
    #      'BASE_URL': "http://%s" % Site.objects.get_current().domain
    #  }
    #  # or if you don't want to use 'sites' app
    return {
         'BASE_URL': request.build_absolute_uri("/").rstrip("/")
    }