from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^$', 'mysite.polls.views.startSearch'),
    (r'^search/$', 'mysite.polls.views.query'),
    (r'^searchTitle/$', 'mysite.polls.views.queryTitle'),
    (r'^searchAbstract/$', 'mysite.polls.views.queryAbstract'),
    (r'^searchAll/$', 'mysite.polls.views.queryAll'),
    (r'^keywordSearch/$', 'mysite.polls.views.search_newVersion'),
    (r'^keywordSearch_(\S+)/$', 'mysite.polls.views.searchCloud'),
    (r'^p2pKeywordSearch/$', 'mysite.polls.views.p2pKeywordSearch'),

    (r'^citing(\S+)/$', 'mysite.polls.views.getCitedBy'),
)
