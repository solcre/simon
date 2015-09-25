from django.core.management.base import BaseCommand
from simon_app.models import Results, TestPoint, SpeedtestTestPoint


class Command(BaseCommand):
    def make_request(self, url, method="GET", count=10):
        import httplib, datetime

        t0 = datetime.datetime.now()
        results = []

        for n in range(count):
            conn = httplib.HTTPConnection(url)
            conn.request(method, "/")

            t1 = datetime.datetime.now()
            r = conn.getresponse()
            diff = datetime.datetime.now() - t1

            results.append(diff.total_seconds() * 1000) # millis
            conn.close()

        return r, results

    def handle(self, *args, **options):

        from sys import stdout
        import numpy

        for tp in SpeedtestTestPoint.objects.all():

            try:
                url = tp.ip_address

                gets = []
                heads = []
                N = 10
                for i in range(N):

                    stdout.write("\r%.2f%%" % (100.0 * i / N))
                    stdout.flush()

                    _r, rtt_get = self.make_request(url, method="GET", count=10)
                    _r, rtt_head = self.make_request(url, method="HEAD", count=10)

                    gets += rtt_get
                    heads += rtt_head

                print "\rGET: %.0f ms \t HEAD: %.0f \t (%s)" % (numpy.average(gets), numpy.average(heads), tp.speedtest_url)

                print gets
                print heads

            except KeyboardInterrupt:
                raise
            except:
                continue

            exit(0)