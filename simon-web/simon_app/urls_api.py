__author__ = 'agustin'

from django.conf.urls import patterns, include, url

latency_view = 'simon_app.views.latency'
latency_urls = patterns(r'',

                        url(r'^autnum/(?P<asn_origin>[0-9]+)/(?P<asn_destination>[0-9]+)/$', 'simon_app.api_views.ases'),

                        url(r'^(?P<country>[A-Z]{2})/(?P<ip_version>[46])/(?P<year>[0-9]{4})/(?P<month>[0-9]{1,2})$', latency_view),
                        url(r'^(?P<country>[A-Z]{2})/(?P<ip_version>[46])/(?P<year>[0-9]{4})$', latency_view),
                        url(r'^(?P<country>[A-Z]{2})/(?P<ip_version>[46])$', latency_view),
                        url(r'^(?P<country>[A-Z]{2})/(?P<year>[0-9]{4})/(?P<month>[0-9]{1,2})$', latency_view),
                        url(r'^(?P<country>[A-Z]{2})/(?P<month>[0-9]{1,2})$', latency_view),
                        url(r'^(?P<country>[A-Z]{2})/(?P<ip_version>[46])/(?P<month>[0-9]{1,2})$', latency_view),
                        url(r'^(?P<country>[A-Z]{2})/(?P<year>[0-9]{4})$', latency_view),
                        url(r'^(?P<country>[A-Z]{2})$', latency_view),

                        url(r'^(?P<ip_version>[46])/(?P<year>[0-9]{4})/(?P<month>[0-9]{1,2})$', latency_view),
                        url(r'^(?P<ip_version>[46])/(?P<year>[0-9]{4})$', latency_view),
                        url(r'^(?P<ip_version>[46])$', latency_view),
                        url(r'^(?P<year>[0-9]{4})/(?P<month>[0-9]{1,2})$', latency_view),
                        url(r'^(?P<month>[0-9]{1,2})$', latency_view),
                        url(r'^(?P<ip_version>[46])/(?P<month>[0-9]{1,2})$', latency_view),
                        url(r'^(?P<year>[0-9]{4})$', latency_view),
                        url(r'^$', latency_view)
)

# Final URLs object
urlpatterns = patterns('',
                       url(r'^$', 'simon_app.views.api'),
                       url(r'^latency/', include(latency_urls)),
)