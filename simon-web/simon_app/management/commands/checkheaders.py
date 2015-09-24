from django.core.management.base import BaseCommand
from simon_app.models import Results, TestPoint, SpeedtestTestPoint


class Command(BaseCommand):

    def make_request(self, url, method="GET"):
        import httplib, datetime

        t0 = datetime.datetime.now()

        conn = httplib.HTTPConnection(url)
        conn.request(method, "/")

        t1 = datetime.datetime.now()
        r = conn.getresponse()
        diff = datetime.datetime.now() - t1

        return r, diff.total_seconds() * 1000

    def handle(self, *args, **options):

        for tp in SpeedtestTestPoint.objects.all():
            url = tp.ip_address

            r, rtt_get = self.make_request(url)
            r, rtt_head = self.make_request(url, method="HEAD")
            diff = rtt_get - rtt_head

            print "GET: %.0f ms \t HEAD: %.0f \t Diff: %.0f" % (rtt_get, rtt_head, diff)