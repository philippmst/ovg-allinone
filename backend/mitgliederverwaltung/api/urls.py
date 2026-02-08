from django.conf.urls import include
from django.urls import include, re_path
from rest_framework import routers
from knox import views as knox_views
from api.views import views
from api.views import mitglieder
from api.views import institutionen
from api.views import abos

# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'groups', views.GroupViewSet)
router.register(r'vereinsmitglieder', mitglieder.VereinsMitgliedViewSet)
router.register(r'countries', views.CountryViewSet)
router.register(r'berufe', views.BerufeViewSet)
router.register(r'mitgliedsart', views.MitgliedsartViewSet)
router.register(r'kosten', views.KostenViewSet)
router.register(r'vortragsort', views.VortragsortViewSet)
router.register(r'adresse', views.AdresseViewSet)
router.register(r'institutionen', institutionen.InstitutionenViewSet)
router.register(r'aboheft', abos.AboHeftViewSet)
router.register(r'abonnent', abos.AbonnentViewSet)
router.register(r'offeneposten', views.offenePostenViewSet)
router.register(r'offeneaboposten', abos.OffeneAboPostenViewSet)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    re_path(r'^', include(router.urls)),
    re_path(r'^dashboard/$', views.dashboard, name='dashboard'),
    re_path(r'^auth/register/$', views.RegistrationAPI.as_view()),
    re_path(r'^auth/login/$', views.LoginAPI.as_view()),
    re_path(r'^auth/user/$', views.UserAPI.as_view()),
    re_path(r'^auth/logout/$', knox_views.LogoutView.as_view()),

    re_path(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]
