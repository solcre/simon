from simon_app.models import *
from simon_app.models_notifications import *
from django.contrib import admin


class ResultsAdmin(admin.ModelAdmin):
    fields = ()
    readonly_fields = ('as_origin', 'as_destination')


admin.site.register(Country)
# admin.site.register(ThroughputResults)
admin.site.register(Results, ResultsAdmin)
admin.site.register(TracerouteResult)
admin.site.register(TestPoint)
# admin.site.register(Images)
# admin.site.register(Images_in_TestPoints)
admin.site.register(OfflineReport)
admin.site.register(Configs)
admin.site.register(AS)

admin.site.register(Params)

# admin.site.register(Notification)
# admin.site.register(Alert)
# admin.site.register(Error)
# admin.site.register(Success)