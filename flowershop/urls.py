from django.conf.urls import patterns, include, url
from admin_super import admin_super
from admin_client import admin_client
from django.conf import settings

from common.views import ViewDefault, ViewRobots
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.static import static
from filebrowser.sites import site
from common.urls import ajax_urlpatterns


urlpatterns = staticfiles_urlpatterns()

if settings.LOCAL:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += ajax_urlpatterns()


# import socketio.sdjango
# socketio.sdjango.autodiscover()
# urlpatterns += patterns('', url("^socket\.io", include(socketio.sdjango.urls)),)



urlpatterns += patterns('',
                        (r'^grappelli/', include('grappelli.urls')),
                        url(r'^admin/filebrowser/', include(site.urls)),

                        url(r'^admin/', include(admin_super.urls)),
                        url(r'^client/', include(admin_client.urls)),

                        url(r'^robots.txt', ViewRobots.as_view(), name='view_robots'),
                        url(r'^accs/', include('password_reset.urls')),

                        url(r'', include('frontend.urls',  namespace='frontend')),
                        url(r'', ViewDefault.as_view(), name='view_default'),


)