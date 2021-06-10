from django.conf import settings

def reverse_proxy_digital_ocean_alterlink(get_response):
    def process_request(request):
        if not settings.DEBUG:
            request.META['REMOTE_ADDR'] = request.META['HTTP_X_REAL_IP']
        return get_response(request)
    return process_request