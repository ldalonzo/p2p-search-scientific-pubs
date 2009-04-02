from django.conf.urls.defaults import *

#from django.contrib import admin

#admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^mysite/', include('mysite.foo.urls')),
    (r'^$', 'mysite.polls.views.startSearch'),
    (r'^search/$', 'mysite.polls.views.query'),
    (r'^searchTitle/$', 'mysite.polls.views.queryTitle'),
    (r'^searchAbstract/$', 'mysite.polls.views.queryAbstract'),
    (r'^searchAll/$', 'mysite.polls.views.queryAll'),
    (r'^keywordSearch/$', 'mysite.polls.views.search_newVersion'),
    (r'^keywordSearch_(\S+)/$', 'mysite.polls.views.searchCloud'),
    (r'^p2pKeywordSearch/$', 'mysite.polls.views.p2pKeywordSearch'),
    
    #(r'^searchIDF/$', 'mysite.polls.views.queryIDF'),
    #(r'^search/cited(\w+)$', 'mysite.polls.views.getCitedBy'),
    #(r'^searchTitle/cited(\w+)$', 'mysite.polls.views.getCitedBy'),
    #(r'^searchAbstract/cited(\w+)$', 'mysite.polls.views.getCitedBy'),
    #(r'^searchAll/cited(\w+)$', 'mysite.polls.views.getCitedBy'),
    
    (r'^citing(\S+)/$', 'mysite.polls.views.getCitedBy'),
    
    
    
    #(r'^mysite/form$', 'mysite.polls.views.contact'),
    #(r'^mysite/$', 'mysite.polls.views.hello'),
    #(r'^mysite/search/$', 'mysite.polls.views.query'),
    #(r'^(?P<poll_id>\d+)/vote/$', 'mysite.polls.views.vote'),
    
    # Uncomment this for admin:
    # (r'^admin/(.*)', admin.site.root),
)
