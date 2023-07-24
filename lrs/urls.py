from django.conf.urls import include, url
from . import views


urlpatterns = [
    url(r'^$', views.home),
    url(r'^statements/more/(?P<more_id>.{32})$', views.statements_more, name='statements_more'),
    url(r'^statements', views.statements, name='statements'),
    url(r'^activities/state', views.activity_state, name='activity_state'),
    url(r'^activities/profile',  views.activity_profile, name='activity_profile'),
    url(r'^activities',  views.activities, name='activities'),
    url(r'^agents/profile', views.agent_profile,  name='agent_profile'),
    url(r'^agents', views.agents, name='agents'),
    url(r'^register', views.register, name='register'),
    url(r'^regclient', views.reg_client, name='reg_client'),
    url(r'^statementvalidator', views.stmt_validator, name='stmt_validator'),

    # url(r'^about', views.about),
    # url(r'^OAuth/', include('oauth_provider.urls', namespace='oauth')),
    # # just urls for some user interface and oauth2... not part of xapi
    # url(r'^oauth2/', include('oauth2_provider.provider.oauth2.urls', namespace='oauth2')),
    # url(r'^register', views.register),
    # url(r'^regclient2', views.reg_client2),
    # # url(r'^regclient', views.reg_client),
    # url(r'^statementvalidator', views.stmt_validator),
    # url(r'^me/statements', views.my_statements),
    # url(r'^me/delete/statements', views.my_delete_statements),
    # url(r'^me/download/statements', views.my_download_statements),
    # url(r'^me/activities/states', views.my_activity_states),
    # url(r'^me/activities/state', views.my_activity_state),
    # url(r'^me/apps', views.my_app_status),
    # url(r'^me/tokens2', views.delete_token2),
    # url(r'^me/tokens', views.delete_token),
    # url(r'^me/clients', views.delete_client),
    # url(r'^me', views.me)
]
