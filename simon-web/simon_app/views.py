# -*- encoding: utf-8 -*-

from __future__ import division

import math
import re
from smtplib import SMTPException
from socket import gaierror

from django.contrib.gis.geoip import GeoIP
from django.core.mail import EmailMultiAlternatives
from django.http import HttpResponse
from django.shortcuts import redirect, render_to_response, render
from django.views.decorators.csrf import csrf_exempt
from lxml import etree

from lib.helpers import getContext
from netaddr import IPAddress, IPNetwork
from ntplib.ntplib import *
from simon_app.api_views import \
    country_latency_chart as  country_latency_chart_api, \
    region_latency_chart as region_latency_chart_api, tables as tables_api, \
    throughput_json as throughput_json_api, \
    inner_latency_chart as inner_latency_chart_api, \
    servers_locations_maps as servers_locations_maps_api, \
    region_throughput_chart as region_throughput_chart_api, \
    web_configs as web_configs_api, web_points as web_points_api, \
    ntp_points as ntp_points_api, throughput_tables as throughput_tables_api, \
    latency as latency_api, throughput as throughput_api, \
    throughput_by_country_chart as throughput_by_country_chart_api, getCountry
from simon_app.functions import KMG2bps, inLACNICResources, whoIs, bps2KMG
from simon_app.javascript_latency import CountryForm
from simon_app.models import *
from simon_app.reportes import ResultsForm, AddNewWebPointForm, AddNewNtpPointForm, GMTUY, CountryDropdownForm, ReportForm
import simon_project.settings as settings
from _socket import timeout


def lab(request):
    """
    """
    return render_to_response('lab.html')


def thanks(request):
    return render_to_response('thanks.html', getContext(request))


def browserstack(request):
    return render_to_response('browserstack.html', getContext(request))


def articles(request):
    return render_to_response('articles.html', getContext(request))

# ##################
# TRACEROUTE FORM #
# ##################

from reportes import UploadFileForm


@csrf_exempt
def traceroute(request):
    """
        View donde son posteados los archivos de traceroute
    """
    if request.method == 'POST':
        fileName = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        with open("%s/data/traceroute/%s" % (settings.STATIC_ROOT, fileName), 'w') as destination:
            for chunk in request.FILES['file'].chunks():
                destination.write(chunk)
            destination.close()

            saveTracerouteResults(request, "%s/data/traceroute/%s" % (settings.STATIC_ROOT, fileName))
        return redirect("simon_app.views.thanks")
    else:
        traceroutes = TracerouteResult.objects.clean().order_by('-date_test')[:5]

        return render(request, 'traceroute.html', {'form': form, 'traceroutes': traceroutes})


def traceroute_curl(request):
    ip = request.META['REMOTE_ADDR']
    l_root_4 = "199.7.83.42"
    l_root_6 = "2001:500:3::42"
    run4 = 1
    run6 = 0
    if ':' in ip:
        l_root = l_root_6
        run6 = 1
    else:
        l_root = l_root_4

    return render(request, 'traceroute_curl.html',
                  {
                      'l_root': l_root,
                      'run4': run4,
                      'run6': run6,
                      'domain': settings.SIMON_URL
                  },
                  content_type='text/plain')


def saveTracerouteResults(request, fileName):
    """
        Traceroute calculations
    """
    from IPy import IP

    f = open("%s" % (fileName), 'r')
    lines = f.readlines()
    f.close()

    ip_origin = request.META['REMOTE_ADDR']
    print "origen : %s" % ip_origin
    for line in lines:
        fields = line.split()
        try:
            ip_destination = fields[1]
            print "destino : %s" % ip_destination

            rtts = []
            for field in fields[2:]:
                try:
                    rtts.append(float(field))
                except ValueError:
                    pass

            if len(rtts) > 0:
                stddev = 0

                if len(rtts) > 1:
                    devs = []
                    mean = sum(rtts) / float(len(rtts))
                    for r in rtts:
                        dev = (r - mean) ** 2
                        devs.append(dev)
                    stddev = math.sqrt(sum(devs) / (len(devs) - 1))

                median_rtt = 0
                if len(rtts) == 1:
                    median_rtt = rtts[0]
                elif len(rtts) == 2:
                    median_rtt = mean
                elif len(rtts) == 3:
                    median_rtt = rtts[1]

                try:
                    country_origin = whoIs(ip_origin)['country']
                    country_destination = whoIs(ip_destination)['country']
                except timeout:
                    country_origin = 'XX'
                    country_destination = 'XX'

                r = Results()

                r.date_test = datetime.datetime.now()
                r.version = '1'
                r.ip_origin = ip_origin
                r.ip_destination = ip_destination
                r.testype = 'traceroute'
                r.number_probes = len(rtts) / 2  # counting 'ms' fields
                r.rtt_min = min(rtts)
                r.rtt_max = max(rtts)
                r.rtt_ave = mean
                r.dev_rtt = stddev
                r.median_rtt = median_rtt
                r.packet_loss = 3 - r.number_probes
                r.country_origin = country_origin
                r.country_destination = country_destination
                r.ip_version = IP(ip_destination).version()
                r.tester = 'Traceroute'
                r.tester_version = '1'

                r.save()

                print r

        except ValueError as ve:
            print ve
            pass


def servers_locations_maps(request):
    result = servers_locations_maps_api(request)
    return HttpResponse(result, mimetype="application/json")


def region_throughput_chart(request):
    result = region_throughput_chart_api(request)
    return HttpResponse(result, mimetype="application/json")


def throughput_by_country_chart(request):
    result = throughput_by_country_chart_api(request)
    return HttpResponse(result, mimetype="application/json")


def web_points(request, amount, ip_version):
    result = web_points_api(request, amount, ip_version)
    return HttpResponse(result)


def ntp_points(request):
    result = ntp_points_api(request)
    return HttpResponse(result, mimetype="application/json")


def web_configs(request):
    response = web_configs_api(request)
    return HttpResponse(response)


def api(request):
    return render_to_response('api.html', getContext(request))


def country_latency_chart(request, country):
    result = country_latency_chart_api(request, country)
    return HttpResponse(result, mimetype="application/json")


def region_latency_chart(request):
    result = region_latency_chart_api(request)
    return HttpResponse(result, mimetype="application/json")


def inner_latency_chart(request):
    result = inner_latency_chart_api(request)
    return HttpResponse(result, mimetype="application/json")


def latency(request, country='all', ip_version=4, year=2009, month=01):
    return latency_api(request, country, ip_version, year, month)


def throughput(request, country='all', ip_version=4, year=2009, month=01):
    return throughput_api(request, country, ip_version, year, month)


def tables(request, country_iso, ip_version, year, month, tester, tester_version):  # , test_type):
    table_json, ip_version, country_name, date, now, tester, tester_version = tables_api(request, country_iso, ip_version, year, month, tester, tester_version)
    return render_to_response('table.html', {'json': table_json, 'ip_version': ip_version, 'country': country_name, 'date': date, 'now': now, 'tester': tester, 'tester_version': tester_version}, getContext(request))


def throughput_json(request, country_iso, ip_version, year, month, tester, tester_version):  # , test_type):
    json = throughput_json_api(request, country_iso, ip_version, year, month, tester, tester_version)
    return HttpResponse(json, mimetype="application/json")


def throughput_tables(request, country_iso, ip_version, year, month, tester, tester_version):  # , test_type):
    json, ip_version, country_name, date, now, tester, tester_version = throughput_tables_api(request, country_iso, ip_version, year, month, tester, tester_version)
    return render_to_response('table.html', {'json': json, 'ip_version': ip_version, 'country': country_name, 'date': date, 'now': now, 'tester': tester, 'tester_version': tester_version}, getContext(request))


def err404(request):
    return render_to_response('404.html')


@csrf_exempt
def post_xml_result(request):
    """
    View que recibe los datos de las mediciones
    """

    if (request.method != 'POST'):  # and request.method != 'GET'
        return HttpResponse("invalid method: %s" % request.method)

    schema_file = '%s/SimonXMLSchema.xsd' % settings.STATIC_ROOT
    # IMPORTANTE ARREGLAR EL SCHEMA DEL PAIS!!
    with open(schema_file) as f_schema:
        schema_doc = etree.parse(f_schema)
        schema = etree.XMLSchema(schema_doc)
        parser = etree.XMLParser(schema=schema)

        f_source = request.body

        try:
            simon = etree.fromstring(str(f_source), parser)
            tests_list = simon.xpath("test")
            for tests in tests_list:
                result = Results()

                result.version = simon.find('version').text
                result.set_date_time(simon.find('date').text, simon.find('time').text)
                result.country_origin = simon.find('local_country').text

                for field in tests:
                    result.set_data_test(field.tag, field.text)

                result.country_destination = TestPoint.objects.get(ip_address=result.ip_destination).country
                result.tester = simon.find('tester').text
                result.tester_version = simon.find('tester_version').text
                result.as_origin = AS.objects.get_as_by_ip(result.ip_origin)
                result.as_destination = AS.objects.get_as_by_ip(result.ip_destination)
                result.user_agent = simon.find('user_agent').text
                result.url = simon.find('url').text

                print result.url

                result.save()
        except etree.XMLSyntaxError as e:
            # this exception is thrown on schema validation error
            print e
        except Exception as e:
            print e

    return HttpResponse("END")


@csrf_exempt
def post_traceroute(request):
    """
    View que recibe los datos de traceroute.
    Asume que la interfaz que postea los resultados es la misma que originó los tracroutes
    """

    if (request.method != 'POST'):
        return HttpResponse("invalid method: %s" % request.method)

    try:
        output = request.POST['output']
        ip_origin = request.META['REMOTE_ADDR']
    except Exception as e:
        return HttpResponse("ERROR")

    tracerouteResult = TracerouteResult()
    tracerouteResult.output = output
    tracerouteResult.ip_origin = ip_origin
    # tracerouteResult.ip_destination = tracerouteResult.parse().dest_ip

    tracerouteResult.save()

    return HttpResponse("Thanks!\n")


@csrf_exempt
def post_xml_throughput_result(request):
    if (request.method != 'POST'):
        return HttpResponse("invalid method: %s" % request.method)

    schema_file = '%s/SimonXMLSchemaThroughput.xsd' % settings.STATIC_ROOT

    with open(schema_file) as f_schema:
        schema_doc = etree.parse(f_schema)
        schema = etree.XMLSchema(schema_doc)
        parser = etree.XMLParser(schema=schema)

        f_source = request.raw_post_data
        # with open(source_file) as f_source:
        try:
            # simon = etree.parse(f_source, parser)
            # simon = simon.getroot()
            simon = etree.fromstring(f_source, parser)

            tests_list = simon.xpath("test")

            for tests in tests_list:
                result = ThroughputResults()

                # seteo los valores de simon
                result.version = simon.find('version').text
                result.set_date_time(simon.find('date').text, simon.find('time').text)
                result.country_origin = simon.find('local_country').text
                result.ip_origin = request.META['REMOTE_ADDR']

                for field in tests:
                    result.set_data_test(field.tag, field.text)

                # seteo el pais de destino
                result.country_destination = TestPoint.objects.filter(ip_address=result.ip_destination).get().country
                result.tester = simon.find('tester').text
                result.tester_version = simon.find('tester_version').text

                result.save()
        except etree.XMLSyntaxError as e:
            # this exception is thrown on schema validation error
            print e
        except Exception as e:
            print e

    return HttpResponse("END")


@csrf_exempt
def post_offline_testpoints(request):
    if (request.method != 'POST'):  # and request.method != 'GET'
        return HttpResponse("invalid method: %s" % request.method)

    schema_file = '%s/SimonXMLSchemaOfflinePoint.xsd' % settings.STATIC_ROOT

    with open(schema_file) as f_schema:
        schema_doc = etree.parse(f_schema)
        schema = etree.XMLSchema(schema_doc)
        parser = etree.XMLParser(schema=schema)

        f_source = request.body
        try:
            report = etree.fromstring(f_source, parser)

            points = report.xpath("point")

            for point in points:
                try:
                    dbPoint = OfflineReport.objects.get(ip_address=point.find('destination_ip').text)
                    # match
                    dbPoint.report_count += 1

                    if True:  # dbPoint.report_count >= settings.TESTPOINT_OFFLINE_OCCURRENCES:##############################################
                        # alarm
                        # generate the token
                        dbTestPoint = TestPoint.objects.get(ip_address=dbPoint.ip_address)

                        dbTestPoint.enabled = False  ###################################33
                        #                         dbTestPoint.save()  #########################################33

                        #                         token = ActiveTokens(token_value=''.join(random.choice('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz') for i in range(settings.TOKEN_LENGTH)), token_expiration=datetime.datetime.now() + datetime.timedelta(minutes=settings.TOKEN_TIMEOUT), testpoint=dbTestPoint)
                        #                         token.save()
                        #
                        #                         minutes = math.ceil((token.token_expiration - datetime.datetime.now()).total_seconds() / 60)
                        #
                        #                         country = Country.objects.get(iso=dbTestPoint.country)
                        #
                        #                         asunto = 'Server offline notification - Simon Project'
                        #                         texto = 'This message has been sent to the Simon Project mailing list.'
                        #                         texto_HTML = '<p>The point <strong>%s</strong> in %s has been reported offline %s times. To unsubscribe the point please <a href="%s/%s">click here</a>. Note that the link will expire after %s minutes</p>' % (dbTestPoint.ip_address, country.printable_name, dbPoint.report_count, settings.UNSUBSCRIBE_TESTPOINT_URL, token.token_value, minutes)

                        #                         try:
                        #                             msg = EmailMultiAlternatives(asunto, texto, settings.DEFAULT_FROM_EMAIL, [settings.SERVER_EMAIL])
                        #                             msg.attach_alternative(texto_HTML, "text/html")
                        #                             msg.content_subtype = "html"  # Main content is now text/html
                        #                             msg.send()############################################
                        #                         except SMTPException as e:
                        #                             print e

                        #                     dbPoint.save()
                except OfflineReport.DoesNotExist:
                    # new report
                    offlinePoint = OfflineReport()
                    offlinePoint.ip_address = point.find('destination_ip').text
                    offlinePoint.date_reported = datetime.datetime.now(GMTUY())  # point.find('date').text
                    offlinePoint.report_count = 1
                    offlinePoint.save()

        except etree.XMLSyntaxError as e:
            # this exception is thrown on schema validation error
            print 'Error when matching with schema.'
            print e
        except Exception as e:
            print e

    return HttpResponse("END")


def home(request):
    return render_to_response('home.html', getContext(request))


def objectives(request):
    return render_to_response('objectives.html', getContext(request))


def participate(request):
    return render_to_response('participate.html', getContext(request))


def reports(request):
    import json, requests
    ip = request.META.get('REMOTE_ADDR', None)
    latency_histogram_applet = latency_histogram_js = ""

    if request.method == 'POST':

        id = request.POST['country']
        year = int(request.POST['year'])
        cc = Country.objects.get(id=id).iso

        latency_histogram_js = Chart.objects.javascriptChart(cc=cc, year=year, divId='latency_histogram_js')

        latency_histogram_applet = Chart.objects.appletChart(cc=cc, year=year, divId='latency_histogram_applet')

        form = ReportForm(request.POST)

    else:
        form = ReportForm()

    return render_to_response('reports.html', {'form': form,
                                               'latency_histogram_applet': latency_histogram_applet,
                                               'latency_histogram_js': latency_histogram_js
    }, getContext(request))


def charts_reports(request):
    import datetime
    import json
    # ###########
    # DROPDOWN #
    ############

    ip = request.META.get('REMOTE_ADDR', None)
    g = GeoIP()

    try:
        cc = g.country(ip)['country_code']
        print "Accediendo desde %s" % cc
        id_country = Country.objects.get(iso=cc)
        countries_dropdown = CountryDropdownForm(initial={'country': id_country})
    except (Country.DoesNotExist, TypeError):
        # IP is probably a local address
        countries_dropdown = CountryDropdownForm()
    except:
        countries_dropdown = CountryDropdownForm()

    ############
    # HEATMAPS #
    ############

    import json

    key = 'heatmap_countries'
    heatmap_countries = Params.objects.get(config_name=key)

    key = 'heatmap_values'
    heatmap_values = json.loads("{ \"%s\" : %s}" % (key, Params.objects.get(config_name=key)))

    key = 'heatmap_asns'
    heatmap_asns = Params.objects.get(config_name=key)

    key = 'heatmap_asns_values'
    heatmap_asns_values = Params.objects.get(config_name=key)  #json.loads("{ \"%s\" : %s}" % (key, Params.objects.get(config_name=key)))

    ####### 
    # MAP #
    #######

    testpoints = TestPoint.objects.all()
    countries = {}
    for tp in testpoints:
        if tp.country is not None:
            cc = tp.country.encode("utf8")
            try:
                countries[cc] += 1
            except KeyError:
                countries[cc] = 1
    items = countries.items()
    countries = ""
    for i in items:
        countries += "%s," % (str(list(i)))

    year = datetime.datetime.now().year
    years = range(2009, year + 1)

    ##############
    # Histograms #
    ##############
    import requests

    now = datetime.datetime.now()
    a_year_ago = now - datetime.timedelta(days=365)
    rtts_applet = Results.objects.applet().values_list('ave_rtt', flat=True)
    rtts_js = Results.objects.javascript().filter(date_test__gte=a_year_ago).values_list('ave_rtt', flat=True)
    url = "http://127.0.0.1:8001/charts/hist/code"

    data = dict(data=json.dumps([list(rtts_applet)]),
                divId='latency_histogram_applet',
                labels=json.dumps(['Regional latency']),
                colors=json.dumps(['orange']))
    latency_histogram_applet = requests.post(url, data=data).text

    data = dict(data=json.dumps([list(rtts_js)]),
                divId='latency_histogram_js',
                labels=json.dumps(['Regional latency']),
                colors=json.dumps(['orange']))
    latency_histogram_js = requests.post(url, data=data).text

    # data = dict(data=json.dumps([list(rtts_inner)]),
    #             divId='latency_histogram_inner',
    #             labels=json.dumps(['Regional latency']),
    #             colors=json.dumps(['orange']))
    # latency_histogram_inner = requests.post(url, data=data).text

    ############
    # RESPONSE #        
    ############

    return render_to_response('charts.html', {
        'heatmap_asns': heatmap_asns,
        'heatmap_asns_values': heatmap_asns_values,
        'heatmap_countries': heatmap_countries,
        'heatmap_values': heatmap_values['heatmap_values'],
        'countries_dropdown': countries_dropdown,
        'countries': countries,
        'years': years,

        'latency_histogram_applet': latency_histogram_applet,
        'latency_histogram_js': latency_histogram_js
        # 'latency_histogram_inner' : latency_histogram_inner
    }, getContext(request))


def charts_reports_bandwidth(request):
    return render_to_response('charts_reports_bandwidth.html', getContext(request))


def form(request):
    # Processes the form and redirects to the table
    if request.method == 'POST':  # If the form has been submitted...
        form = ResultsForm(request.POST)  # A form bound to the POST data
        # if form.is_valid(): # All validation rules pass
        # Process the data in form.cleaned_data
        country = str(form.data['countries'])
        ip_version = str(form.data['ip_version'])
        # tester includes tester version
        tester = str(form.data['tester'])
        # tester_version = str(form.data['tester_version'])
        year = str(form.data['year'])
        month = str(form.data['month'])
        # test_type = form.data['test_type']

        url = settings.URL_PFX + '/results/' + country + '/' + ip_version + '/' + year + '/' + month + '/' + tester  # + '/' + test_type
        url = re.sub('\s+', '', url)
        return redirect(url)
    else:
        form = ResultsForm()  # An unbound form

    # return render(request, 'home.html', {'form': form})
    return render_to_response('home.html', {'form': form}, getContext(request))


def throughput_form(request):
    # Processes the form and redirects to the table
    if request.method == 'POST':  # If the form has been submitted...
        form = ResultsForm(request.POST)  # A form bound to the POST data
        # if form.is_valid(): # All validation rules pass
        # Process the data in form.cleaned_data
        country = str(form.data['countries'])
        ip_version = str(form.data['ip_version'])
        # tester includes tester version
        tester = str(form.data['tester'])
        # tester_version = str(form.data['tester_version'])
        year = str(form.data['year'])
        month = str(form.data['month'])
        # test_type = form.data['test_type']

        url = settings.URL_PFX + '/throughputresults/' + country + '/' + ip_version + '/' + year + '/' + month + '/' + tester  # + '/' + test_type
        url = re.sub('\s+', '', url)
        return redirect(url)
    else:
        form = ResultsForm()  # An unbound form

    # return render(request, 'home.html', {'form': form})
    return render_to_response('home.html', {'form': form}, getContext(request))


# Forms for point submitting
def add_new_webpoint_form(request):
    title = 'Agregar Nuevo Punto Web'
    text = "Para registrar su servidor como un punto de testing NTP, complete el siguiente formulario. Una vez completado el formulario, nuestro equipo lo evaluará y lo pondrá a disposición de la comunidad para que se realicen tests sobre el. Su servidor formara parte de los 400 servidores que conforman este proyecto. Queremos recordarle que los tests no son demasiado frecuentes como para afectar la performance se su servidor."
    web_form = AddNewWebPointForm()
    action = settings.URL_PFX + "/addnewwebpoint"  # form action

    return render_to_response('addpoint.html', {'form': web_form, 'action': action, 'title': title, 'text': text}, getContext(request))


def add_new_ntppoint_form(request):
    title = 'Agregar Nuevo Punto Ntp'
    text = "Para registrar su servidor como un punto de testing NTP, complete el siguiente formulario. Una vez completado el formulario, nuestro equipo lo evaluará y lo pondrá a disposición de la comunidad para que se realicen tests sobre el. Su servidor formara parte de los 400 servidores que conforman este proyecto."
    ntp_form = AddNewNtpPointForm()
    action = settings.URL_PFX + "/addnewntppoint"  # form action

    return render_to_response('addpoint.html', {'form': ntp_form, 'action': action, 'title': title, 'text': text}, getContext(request))


# Views for point submitting
def add_new_webpoint(request):
    if request.method == 'POST':
        MINIMUM_BANDWIDTH = 1000000  # 1Mbps
        MEETS_BANDWITH = False
        IN_LACNIC_RESOURCES = False
        HAS_IP = False

        form = AddNewWebPointForm(request.POST)
        volunteer_email = form.data['email']


        # end with '/'. This way we avoid paths such as /simon//images...
        images_path = form.data['images_path']
        if str(images_path)[-1] is not '/':
            images_path = '%s/' % images_path

        # check if the URL is valid (example: is not 'http://.....') and free of typos 
        url = form.data['server_url']
        if str(url)[:7] is 'http://':
            url = str(url)[7:]

        # Chack bandwidth requirements
        bandwidth = form.data['bandwidth']
        unit = form.data['unit']
        bps = KMG2bps('%s %s' % (bandwidth, unit))
        if bps > MINIMUM_BANDWIDTH:
            MEETS_BANDWITH = True
        else:
            print '%s doesn\'t meet the minimum bandwidth of %s' % (url, bps2KMG(MINIMUM_BANDWIDTH))

        country_printable = Country.objects.get(id=form.data['country']).printable_name

        try:
            # answers may hold multiple addresses for the same server (IPv4 and IPv6, or multiple addresses of the same kind)
            answers = socket.getaddrinfo(url, 80, 0, 0, socket.SOL_TCP)

            for answer in answers:
                testPoint = TestPoint()
                testPoint.description = form.data['organization']
                testPoint.url = url
                print answer[4][0]
                if answer[4][0] is not None:
                    testPoint.ip_address = answer[4][0]
                    HAS_IP = True
                else:
                    print 'Couldn\'t find an address for %s' % url

                    # check if point address is under LACNIC's resources
                print testPoint.ip_address
                if inLACNICResources(testPoint.ip_address) is True:
                    IN_LACNIC_RESOURCES = True
                else:
                    print '%s not in LACNIC resources' % testPoint.ip_address

                if IN_LACNIC_RESOURCES is not True or MEETS_BANDWITH is not True or HAS_IP is not True:  # triple condition not to repeat all the mailing text....
                    # Error message
                    if IN_LACNIC_RESOURCES is not True:
                        problema = 'la dirección del servidor no forma parte del espacio de direcciones de LACNIC'
                    elif MEETS_BANDWITH is not True:
                        problema = 'el servidor no cumple con el mínimo de ancho de banda requerido'
                    elif HAS_IP is not True:
                        problema = 'no se ha encontrado una dirección IP para la URL provista'

                    # email volunteer
                    asunto = 'Su servidor esta siendo estudiado - Proyecto Simón'
                    texto = 'Hemos recibido una petición para agregar su servidor a nuestra lista de servidores. Nuestro equipo ha determinado que por el momento no es apto para integrar la lista de servidores debido a que %s. De todos modos será estudiado, y en caso de ser apto, le notificaremos al respecto. Datos del servidor:Organización: %sURL: %sPaís: %sDirección IP: %s. Muchas gracias por su colaboración. Lo invitamos a seguir siendo partícipe de este proyecto realizando algunos tests.' % (
                        problema, str(testPoint.description), str(testPoint.url), str(country_printable), str(testPoint.ip_address))
                    texto_HTML = '<p>Hemos recibido una petición para agregar su servidor a nuestra lista de servidores. Nuestro equipo ha determinado que por el momento no es apto para integrar la lista de servidores debido a que %s. De todos modos será estudiado, y en caso de ser apto, le notificaremos al respecto.</p><p> <u>Datos del servidor:</u></p><p>Organización: %s</p><p>URL: %s</p><p>País: %s</p><p>Dirección IP: <strong>%s</strong></p><p>Muchas gracias por su colaboración. Lo invitamos a seguir siendo partícipe de este proyecto realizando algunos tests <a href="http://simon.labs.lacnic.net/simon/participate/">aquí</a>.</p>' % (
                        problema, str(testPoint.description), str(testPoint.url), str(country_printable), str(testPoint.ip_address))
                    try:
                        msg = EmailMultiAlternatives(asunto, texto, settings.DEFAULT_FROM_EMAIL, [volunteer_email])
                        msg.attach_alternative(texto_HTML, "text/html")
                        msg.content_subtype = "html"  # Main content is now text/html
                        msg.send()
                    except SMTPException as e:
                        print e
                    # email admins
                    asunto = 'Aviso de servidor WEB - Proyecto Simón'
                    texto = 'Este mensaje ha sido enviado a la lista de correo del Proyecto Simón. El punto %s en %s quiere formar parte de la lista de servidores WEB, pero %s. Para darle de alta por favor póngase en contacto con %s. Muchas gracias.' % (
                        str(testPoint.ip_address), str(country_printable), problema, str(volunteer_email))
                    texto_HTML = 'Este mensaje ha sido enviado a la lista de correo del Proyecto Simón. <p>El punto <strong>%s</strong> en %s quiere formar parte de la lista de servidores WEB, pero %s. Para darle de alta por favor póngase en contacto con <a href="mailto:%s?subject=Contacto - Proyecto Simón">%s</a>.</p><p>Muchas gracias</p>.' % (
                        str(testPoint.ip_address), str(country_printable), problema, str(volunteer_email), str(volunteer_email))

                    try:
                        msg = EmailMultiAlternatives(asunto, texto, settings.DEFAULT_FROM_EMAIL, [settings.SERVER_EMAIL])  # settings.SERVER_EMAIL
                        msg.attach_alternative(texto_HTML, "text/html")
                        msg.content_subtype = "html"  # Main content is now text/html
                        msg.send()
                    except SMTPException as e:
                        print e

                    # redireccion con error
                    title = 'Ups!'
                    text = '<p>Nuestro equipo ha determinado que por el momento su servidor no es apto para integrar la lista de servidores debido a que %s. De todos modos será estudiado, y en caso de ser apto, le notificaremos al respecto.</p><p>Lo invitamos a participar de este proyecto realizando algunos tests <a href="http://simon.labs.lacnic.net/simon/participate/">aquí</a>.</p><p>Muchas gracias.</p>' % problema
                    button = '<p><button onclick="window.location.href=\'/\'">Volver</button></p>'
                    return render_to_response('general.html', {'title': title, 'text': text, 'button': button}, getContext(request))

                # OK message
                # testPoint.description = form.data['organization']
                try:
                    # cc = whoIs(testPoint.ip_address)['operator']['country']
                    cc = whoIs(testPoint.ip_address)['country']
                    testPoint.country = Country.objects.get(iso=cc).is2o
                except:
                    testPoint.country = '##'
                    print 'Error while retrieving Web server %s address.' % testPoint.ip_address

                testPoint.testtype = 'tcp_web'
                testPoint.enabled = False
                tz = GMTUY()
                testPoint.date_created = datetime.datetime.now(tz)
                # testPoint.url = url
                images = Images.objects.filter(online=True)

                testPoint.save()

                for image in images:
                    image_in_test_points = Images_in_TestPoints()
                    image_in_test_points.testPoint = testPoint
                    image_in_test_points.image = image
                    image_in_test_points.local_path = images_path  # image.name)
                    image_in_test_points.save()

                # email admins
                asunto = 'Notificación de nuevo servidor web - Proyecto Simón'
                texto = 'Este mensaje ha sido enviado a la lista de correo del Proyecto Simón. El punto %s ubicado en %s ha sido agregado a la lista de puntos web de testeo. Para darle de alta por favor hágalo mediante el administrados de Django. Muchas gracias.' % (
                    str(testPoint.ip_address), str(testPoint.country))
                texto_HTML = 'Este mensaje ha sido enviado a la lista de correo del Proyecto Simón. <p>El punto <strong>%s</strong> ubicado en %s ha sido agregado a la lista de puntos web de testeo. Para darle de alta por favor hágalo mediante el administrados de Django. Muchas gracias.' % (
                    str(testPoint.ip_address), str(testPoint.country))

                try:
                    msg = EmailMultiAlternatives(asunto, texto, settings.DEFAULT_FROM_EMAIL, [settings.SERVER_EMAIL])  # 
                    msg.attach_alternative(texto_HTML, "text/html")
                    msg.content_subtype = "html"  # Main content is now text/html
                    msg.send()
                except SMTPException as e:
                    print e

                # email volunteer
                asunto = 'Gracias por su contribución - Proyecto Simón'
                texto = 'Hemos recibido una petición para agregar su servidor a nuestra lista de servidores. Brevemente un miembro de nuestro equipo lo evaluará, y de cumplir los requisitos será agregado a la lista.'
                texto_HTML = '<p>Hemos recibido una petición para agregar su servidor a nuestra lista de servidores. Brevemente un miembro de nuestro equipo lo evaluará, y en caso de cumplir los requisitos será agregado a la lista. Recuerde que los tests consumen muy poco ancho de banda y no afectan la performance de su servidor.</p><p>Datos del servidor:</p><p>Organización: %s</p><p>URL: %s</p><p>País: %s</p><p>Dirección IP: <strong>%s</strong></p><p>Ancho de banda (uplink): %s</p><p>Images uploaded: %s</p><p>Muchas gracias por su colaboración. Lo invitamos a seguir siendo partícipe de este proyecto realizando algunos tests <a href="http://simon.labs.lacnic.net/simon/participate/">aquí</a>.</p>' % (
                    str(testPoint.description), str(testPoint.url), str(testPoint.country), str(testPoint.ip_address), str(bandwidth), str(len(images)))
                try:
                    msg = EmailMultiAlternatives(asunto, texto, settings.DEFAULT_FROM_EMAIL, [volunteer_email])  # volunteer_email
                    msg.attach_alternative(texto_HTML, "text/html")
                    msg.content_subtype = "html"  # Main content is now text/html
                    msg.send()
                except SMTPException as e:
                    print e

        except gaierror:
            print 'Error while retrieving %s IP address.' % form.data['server_url']
        except:
            pass

        # redireccion
        title = 'Gracias por su contribución.'
        text = 'Su servidor web debería comenzar a atender tests prontamente. Le recomendamos que siga contribuyando a la comunidad realizando más tests'
        button = '<p><button onclick="window.location.href='"/"'">Volver</button></p>'
        return render_to_response('general.html', {'title': title, 'text': text, 'button': button}, getContext(request))
        # return render_to_response('general.html', {'title':title, 'text':text}, getContext(request))


def add_new_ntppoint(request):
    if request.method == 'POST':
        form = AddNewNtpPointForm(request.POST)
        testPoint = TestPoint()
        g = GeoIP()
        volunteer_email = form.data['email']

        ok = False

        testPoint.description = '%s, contacto: %s' % (form.data['organization'], form.data['email'])
        testPoint.testtype = 'ntp'

        try:
            c = NTPClient()
            url = form.data['server_url']
            response = c.request(url, version=3)
            testPoint.ip_address = ref_id_to_text(response.ref_id)
            print testPoint.ip_address
        except NTPException:
            ok = False
            print 'Error while retrieving NTP server %s address.' % form.data['server_url']

        testPoint.country = g.country_code(testPoint.ip_address)  # Country.objects.get(id=form.data['country']).iso
        country_printable = Country.objects.get(iso=testPoint.country).printable_name
        testPoint.enabled = False
        testPoint.date_created = datetime.datetime.now()
        testPoint.url = form.data['server_url']

        # check if point address is under LACNIC's resources

        for resource in settings.v4resources:
            if IPAddress(testPoint.ip_address) in IPNetwork(resource):
                ok = True
        for resource in settings.v6resources:
            if IPAddress(testPoint.ip_address) in IPNetwork(resource):
                ok = True

                # if ok is not True:
                #            # email volunteer
                #            asunto = 'Su servidor esta siendo estudiado - Proyecto Simón'
                #            texto = 'Hemos recibido una petición para agregar su servidor a nuestra lista de servidores. Nuestro equipo ha determinado que por el momento no es apto para integrar la lista de servidores debido a que su dirección no forma parte del espacio de direcciones de LACNIC. De todos modos será estudiado, y en caso de ser apto, le notificaremos al respecto.'
                #            texto_HTML = '<p>Hemos recibido una petición para agregar su servidor a nuestra lista de servidores. Nuestro equipo ha determinado que por el momento no es apto para integrar la lista de servidores debido a que su dirección no forma parte del espacio de direcciones de LACNIC. De todos modos será estudiado, y en caso de ser apto, le notificaremos al respecto.</p><p>Datos del servidor:</p><p>Organización: %s</p><p>URL: %s</p><p>País: %s</p><p>Dirección IP: <strong>%s</strong></p><p>Muchas gracias por su colaboración. Lo invitamos a seguir siendo partícipe de este proyecto realizando algunos tests <a href="http://simon.labs.lacnic.net/simon/participate/">aquí</a>.</p>' % (str(testPoint.description), str(testPoint.url), str(country_printable), str(testPoint.ip_address))
                #            try:
                #                msg = EmailMultiAlternatives(asunto, texto, settings.DEFAULT_FROM_EMAIL, [volunteer_email])
                #                msg.attach_alternative(texto_HTML, "text/html")
                #                msg.content_subtype = "html"  # Main content is now text/html
                #                msg.send()
                #            except SMTPException as e:
                #                print e
                #
                #            # email admins
                #            asunto = 'Aviso de servidor NTP - Proyecto Simón'
                #            texto = 'Este mensaje ha sido enviado a la lista de correo del Proyecto Simón'
                #            texto_HTML = 'Este mensaje ha sido enviado a la lista de correo del Proyecto Simón. <p>El punto <strong>%s</strong> ubicado en %s quiere formar parte de la lista de servidores NTP, pero no pertenece al espacio de direcciones de LACNIC. Para darle de alta por favor póngase en contacto con <a href="mailto:%s?subject=Contacto - Proyecto Simón">%s</a>. Muchas gracias.' % (str(testPoint.ip_address), str(country_printable), str(volunteer_email), str(volunteer_email))
                #
                #            try:
                #                msg = EmailMultiAlternatives(asunto, texto, settings.DEFAULT_FROM_EMAIL, [settings.SERVER_EMAIL])# settings.SERVER_EMAIL
                #                msg.attach_alternative(texto_HTML, "text/html")
                #                msg.content_subtype = "html"  # Main content is now text/html
                #                msg.send()
                #            except SMTPException as e:
                #                print e
                #
                #            # redireccion con error
                #            title = 'Ups!'
                #            text = '<p>Nuestro equipo ha determinado que por el momento su servidor no es apto para integrar la lista de servidores debido a que su dirección no forma parte del espacio de direcciones de LACNIC. De todos modos será estudiado, y en caso de ser apto, le notificaremos al respecto.</p><p>Lo invitamos a participar de este proyecto realizando algunos tests <a href="http://simon.labs.lacnic.net/simon/participate/">aquí</a>.</p><p>Muchas gracias.</p>'
                #            return render_to_response('general.html', {'title':title, 'text':text}, getContext(request))

        testPoint.save()

        # email admins
        asunto = 'Notificación de nuevo servidor NTP - Proyecto Simón'
        texto = 'Este mensaje ha sido enviado a la lista de correo del Proyecto Simón'
        texto_HTML = 'Este mensaje ha sido enviado a la lista de correo del Proyecto Simón. <p>El punto <strong>%s</strong> ubicado en %s ha sido agregado a la lista de puntos NTP de testeo. Para darle de alta por favor hágalo mediante el administrados de Django. Muchas gracias.' % (
            str(testPoint.ip_address), str(testPoint.country))

        try:
            msg = EmailMultiAlternatives(asunto, texto, settings.DEFAULT_FROM_EMAIL, [settings.SERVER_EMAIL])  # settings.SERVER_EMAIL
            msg.attach_alternative(texto, "text/html")
            msg.content_subtype = "html"  # Main content is now text/html
            msg.send()
        except SMTPException as e:
            print e

        # email volunteer
        asunto = 'Gracias por su contribución - Proyecto Simón'
        texto = 'Hemos recibido una petición para agregar su servidor a nuestra lista de servidores. Brevemente un miembro de nuestro equipo lo evaluará, y de cumplir los requisitos será agregado a la lista.'
        texto_HTML = '<p>Hemos recibido una petición para agregar su servidor a nuestra lista de servidores. Brevemente un miembro de nuestro equipo lo evaluará, y en caso de cumplir los requisitos será agregado a la lista. Recuerde que los tests consumen muy poco ancho de banda y no afectan la performance de su servidor.</p><p>Datos del servidor:</p><p>Organización: %s</p><p>URL: %s</p><p>País: %s</p><p>Dirección IP: <strong>%s</strong></p><p>Muchas gracias por su colaboración. Lo invitamos a seguir siendo partícipe de este proyecto realizando algunos tests <a href="http://simon.labs.lacnic.net/simon/participate/">aquí</a>.</p>' % (
            str(testPoint.description), str(testPoint.url), str(testPoint.country), str(testPoint.ip_address))
        try:
            msg = EmailMultiAlternatives(asunto, texto, settings.DEFAULT_FROM_EMAIL, [volunteer_email])  # volunteer_email
            msg.attach_alternative(texto_HTML, "text/html")
            msg.content_subtype = "html"  # Main content is now text/html
            msg.send()
        except SMTPException as e:
            print e

        # redireccion
        title = 'Gracias por su contribución.'
        text = 'Su servidor web debería comenzar a atender tests prontamente. Le recomendamos que siga contribuyando a la comunidad realizando más tests'
        return render_to_response('general.html', {'title': title, 'text': text}, getContext(request))


def remove_testpoint(request, token):
    try:
        active_token = ActiveTokens.objects.get(token_value=token)
        tz = GMTUY()
        now = datetime.datetime.now(tz)

        if active_token.token_expiration > now:

            testPoint = active_token.testpoint
            testPoint.enabled = False
            testPoint.save()
            active_token.delete()

            return render_to_response('general.html', {'title': 'Thank you', 'text': 'The test point has been removed successfully!'}, getContext(request))
        else:
            return render_to_response('general.html', {'title': 'Sorry', 'text': 'The token corresponding to that test point has expired'}, getContext(request))
    except ActiveTokens.DoesNotExist:
        # Not found
        return redirect('/')


def applet(request):
    # return render(request, 'applet.html')
    return render_to_response('applet.html', getContext(request))


def applet_run(request):
    # return render(request, 'applet.html')
    return render_to_response('applet_run.html', getContext(request))


def javascript_run(request):
    # Get address to pre-select the dropdown menu
    # ip = request.META.get('REMOTE_ADDR', None)
    #
    # try:
    # # cc = whoIs(ip)['operator']['country']
    #     cc = whoIs(ip)['country']
    #     countries = CountryForm(initial={'countries': cc})
    # except (TypeError, HTTPError):
    #     # IP is probably a local address
    #     countries = CountryForm()

    return render_to_response('javascript_run.html', {'countries': CountryForm()}, getContext(request))
