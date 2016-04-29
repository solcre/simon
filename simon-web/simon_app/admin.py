from simon_app.models import *
from django.contrib import admin

class SimonGenericAdmin(admin.ModelAdmin):
    """
        Generic admin covering admin-wide
    """
    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields]

class ResultsAdmin(SimonGenericAdmin):
    fields = ()
    list_display = ['country_origin', 'country_destination', 'as_origin', 'as_destination', 'ave_rtt', 'dev_rtt', 'date_short', 'protocol']
    ordering = ['-date_test', 'country_origin', 'country_destination']
    search_fields = ['country_origin', 'country_destination', 'as_origin', 'as_destination']

    # list_filter = ('enabled',)

    class Media:
        js = (
            # '//ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js',
            # 'http://code.jquery.com/jquery-migrate-1.2.1.js',
            # 'simon_app/admin/js/jquery-adapt.js'
        )


class TracerouteResultAdmin(SimonGenericAdmin):

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields]

    list_display = ['country_origin', 'country_destination', 'as_origin', 'as_destination', 'hop_count']
    search_fields = ['country_origin', 'country_destination', 'as_origin', 'as_destination']

class TracerouteHopAdmin(SimonGenericAdmin):

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields]

    list_display = ['country_origin', 'country_destination', 'as_origin', 'as_destination', 'ip_origin', 'ip_destination', 'ave_rtt', 'dev_rtt', 'date_short', 'protocol']
    search_fields = ['country_origin', 'country_destination', 'as_origin', 'as_destination', 'ip_origin', 'ip_destination']

class TestPointAdmin(SimonGenericAdmin):

    def enable(modeladmin, request, queryset):
        queryset.update(enabled=True)
    enable.short_description = "Habilitar punto de prueba"

    def disable(modeladmin, request, queryset):
        queryset.update(enabled=False)
    disable.short_description = "Deshabilitar punto de prueba"

    def check(modeladmin, request, queryset):
        for q in queryset:
            q.check()
    check.short_description = "Chequear punto de prueba"

    list_display = ['country', 'ip_address', 'autnum', 'city', 'date_short', 'enabled']
    # list_filter = ['country', 'ip_version']
    list_filter = ('country', )
    ordering = ['-date_created', 'enabled']
    actions = [enable, disable, check]
    search_fields = ['country']

class RipeAtlasProbeAdmin(SimonGenericAdmin):
    list_display = ['country_code', 'asn_v4', 'asn_v6', 'prefix_v4', 'prefix_v6']
    search_fields = ['country_code']

class ConfigsAdmin(admin.ModelAdmin):
    def enable(modeladmin, request, queryset):
        queryset.update(config_value="1")

    def disable(modeladmin, request, queryset):
        queryset.update(config_value="0")
    list_display = ['config_name', 'config_value', 'config_description']
    actions = [enable, disable]

from django.contrib.admin.views.main import ChangeList
class InactiveUsersView(ChangeList):
    """
        This view displays the list of inactive users
    """
    def __init__(self, *args, **kwargs):
        super(InactiveUsersView, self).__init__(*args, **kwargs)
        self.list_display = ('description')

    def get_queryset(self, request):
        qs = super(InactiveUsersView, self).get_queryset(request)
        # filter inactive and admin users
        return qs.filter(is_staff=False, is_active=False, is_superuser=False)

class RipeAtlasTokenAdmin(SimonGenericAdmin):
    pass

class RipeAtlasTokenListAdmin(SimonGenericAdmin):
    pass
     # def save_model(self, request, obj, form, change):
     #     print obj
     #     tokens = self.token_list.split(sep="\n")
     #     for token in tokens:
     #         print token
     #         rat = RipeAtlasToken(token=token)
     #         rat.save()

class CommandAuditAdmin(SimonGenericAdmin):
    list_display = ['command', 'date', 'status']

class ASAdmin(SimonGenericAdmin):
    list_display = ['asn', 'network', 'pfx_length', 'date_updated', 'regional']
    search_fields = ['asn', 'network']

admin.site.register(Comment)

admin.site.register(Results, ResultsAdmin)

admin.site.register(TestPoint, TestPointAdmin)
admin.site.register(Configs, ConfigsAdmin)

admin.site.register(ProbeApiPingResult, ResultsAdmin)
admin.site.register(TracerouteResult, TracerouteResultAdmin)
admin.site.register(TracerouteHop, TracerouteHopAdmin)

admin.site.register(SpeedtestTestPoint, TestPointAdmin)
admin.site.register(RipeAtlasPingResult, ResultsAdmin)

admin.site.register(RipeAtlasProbe, RipeAtlasProbeAdmin)

admin.site.register(RipeAtlasToken, RipeAtlasTokenAdmin)
admin.site.register(RipeAtlasTokenList, RipeAtlasTokenListAdmin)

admin.site.register(RipeAtlasMonitoredIds)

admin.site.register(CommandAudit, CommandAuditAdmin)

admin.site.register(AS, ASAdmin)
