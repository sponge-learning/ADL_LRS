from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin


class AllowOriginMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.method == 'OPTIONS':
            return HttpResponse()

    def process_response(self, request, response):
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'HEAD, POST, GET, OPTIONS, DELETE, PUT'
        response['Access-Control-Allow-Headers'] = 'Content-Type,Content-Length,Authorization,If-Match,If-None-Match,X-Experience-API-Version, Accept-Language'
        response['Access-Control-Expose-Headers'] = 'ETag,Last-Modified,Cache-Control,Content-Type,Content-Length,WWW-Authenticate,X-Experience-API-Version, Accept-Language'
        return response