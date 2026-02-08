from django.conf import settings


class HostForwarding(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if settings.DEBUG is False:
            request.META['HTTP_HOST'] = 'members.ovg.at'
        
        response = self.get_response(request)
        response["Access-Control-Allow-Origin"] = "*"

        return response