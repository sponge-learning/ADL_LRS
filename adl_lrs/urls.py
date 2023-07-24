from django.conf import settings
from django.conf.urls import include, url
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView
from . import views
# Uncomment the next two lines to enable the admin (imports admin module in each app):
from django.contrib import admin

admin.autodiscover()

urlpatterns = [
    url(r'^$', RedirectView.as_view(url='/xAPI/')),
    url(r'^XAPI/', include('lrs.urls', namespace='lrs')),
    url(r'^xapi/', include('lrs.urls', namespace='lrs')),
    url(r'^xAPI/', include('lrs.urls', namespace='lrs')),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
]

# Login and logout patterns
urlpatterns += [
    url(r'^accounts/login/$', auth_views.login, name="login"),
    url(r'^accounts/logout/$', views.logout_view, name="logout"),
]

# Allows admins to view attachments in admin console
if settings.DEBUG:
    urlpatterns += [
        url(r'^media/attachment_payloads/(?P<path>.*)$', views.admin_attachments),
    ]
