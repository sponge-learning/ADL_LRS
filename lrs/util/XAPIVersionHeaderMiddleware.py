import re
import urllib.request, urllib.parse, urllib.error
from django.conf import settings
from django.http import HttpResponseBadRequest
from django.utils.deprecation import MiddlewareMixin


class XAPIVersionHeader(MiddlewareMixin):
    def process_request(self, request):
        try:
            version = request.META['X-Experience-API-Version']
        except:
            try:
                version = request.META['HTTP_X_EXPERIENCE_API_VERSION']
                request.META['X-Experience-API-Version'] = version
                request.META.pop('HTTP_X_EXPERIENCE_API_VERSION', None)
            except:
                version = request.META.get('X_Experience_API_Version', None)
                if not version:
                    bdy = urllib.parse.unquote_plus(request.body.decode('utf-8'))
                    bdy_parts = bdy.split('&')
                    for part in bdy_parts:
                        v = re.search('X[-_]Experience[-_]API[-_]Version=(?P<num>.*)', part)
                        if v:
                            version = v.group('num')
                            request.META['X-Experience-API-Version'] = version
                            break
                else:
                    request.META['X-Experience-API-Version'] = version
                    request.META.pop('X_Experience_API_Version', None)

        if not version:
            return HttpResponseBadRequest("X-Experience-API-Version header missing")
        
        regex = re.compile("^1\.0(\.[0-2])?$")
        if not regex.match(version):
            return HttpResponseBadRequest("X-Experience-API-Version is not supported")

    def process_response(self, request, response):
        response['X-Experience-API-Version'] = settings.XAPI_VERSION
        return response
