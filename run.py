

from aniachi.systemUtils import Welcome as W

from wsgiref.simple_server import make_server
from pyramid.config import Configurator
from pyramid.response import Response
from pyramid.httpexceptions import HTTPFound
from pyramid.response import FileResponse
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNotFound
from fbprophet import Prophet
from termcolor import colored
import os

import numpy as np
import pandas as pd

import pkg_resources
import matplotlib.pyplot as plt
import  matplotlib
from io import StringIO
from io import BytesIO
import xml.etree.ElementTree as et

import pickle as pkl
import base64
import traceback
import datetime
import openpyxl
import setuptools
import aniachi

import socket
import pyqrcode
import argparse
import textwrap


port = 8080

file ='mx_us.csv'


@view_config(route_name='hello', renderer='home.jinja2')
def hello_world(request):

    return {'name': 'Running Server','port':port,'pyramid':pkg_resources.get_distribution('pyramid').version
             ,'numpy':np.__version__,'pandas':pd.__version__ ,'favicon':'aniachi_logo.png','matplotlib':matplotlib.__version__,
             'fbprophet':pkg_resources.get_distribution('fbprophet').version,'openpyxl ':openpyxl.__version__,'setuptools':setuptools.__version__,
             'py_common_fetch':pkg_resources.get_distribution('py-common-fetch').version,'host':socket.gethostbyname(socket.gethostname()),
              'pyqrcode':pkg_resources.get_distribution('pyqrcode').version,'argparse':argparse.__version__,'pypng':pkg_resources.get_distribution('pypng').version
            }


#


#





@view_config(route_name='entry')
def entry_point(request):
    return HTTPFound(location='app/welcome')




#



#



def getParamterOrdefault(d,k,v,valid):
    aux = v
    try:
        if (d[k]  in valid): aux = d[k]
    except Exception as e:
        pass
    return aux

#


#

def getIntParameter(d,k,v,r):


    aux=int(v)
    try:
        if isinstance(int(d[k]), int):
            if int(d[k]) in r:
                aux= int(d[k])

    except Exception as e:
        pass

    return aux


def getDataframe():
    return pd.read_csv(os.path.join(os.getcwd(),file))



#



#
def getFilteredDataframe():
    mx_peso = getDataframe()
    mx_peso.columns = ['date', 'mx_usd']
    mx_peso.date = pd.to_datetime(mx_peso['date'], format='%Y-%m-%d')
    # remove dots
    mx_peso = mx_peso[mx_peso['mx_usd'] != '.']
    mx_peso.mx_usd = mx_peso.mx_usd.astype(float)
    return mx_peso


#


#


def getForecastData(days=120):
    mx_peso = getDataframe()
    mx_peso.columns = ['date', 'mx_usd']
    mx_peso.date = pd.to_datetime(mx_peso['date'], format='%Y-%m-%d')
    # remove dots
    mx_peso = mx_peso[mx_peso['mx_usd'] != '.']
    mx_peso.mx_usd = mx_peso.mx_usd.astype(float)
    df = pd.DataFrame.copy(mx_peso, deep=True)
    df.columns = ['ds', 'y']
    prophet = Prophet(changepoint_prior_scale=0.15)
    prophet.fit(df)
    forecast = prophet.make_future_dataframe(periods=days, freq='D')
    forecast = prophet.predict(forecast)

    return  prophet, forecast



@view_config(route_name='dataset')
def datasetServer(request):



    format = getParamterOrdefault(request.params,'format','default',['html','json','xml','serialized','csv','excel'])
    if (format=='csv'):
        df = getDataframe()
        s = StringIO()
        df.to_csv(s)
        r = Response(s.getvalue(), content_type='application/CSV', charset='UTF-8')
    elif (format=='json'):
        df = getDataframe()
        s = StringIO()
        df.to_json(s)
        r = Response(s.getvalue(), content_type='application/json', charset='UTF-8')
    elif (format=='xml'):
        df = getDataframe()
        root = et.Element('root')

        for i, row in df.iterrows():
            data = et.SubElement(root, 'data')
            data.set('iter',str(i))
            date = et.SubElement(data, 'date')
            value = et.SubElement(data, 'value')
            date.text = row[0]
            value.text = row[1]
        r = Response(et.tostring(root), content_type='application/xml', charset='UTF-8')
    elif (format=='html'):
        df = getDataframe()
        s = StringIO()
        df.to_html(s,index=True)
        r = Response(s.getvalue(), content_type='text/html', charset='UTF-8')
    elif (format=='serialized'):

        r = Response(base64.encodebytes(pkl.dumps(getDataframe())).decode('utf-8'), content_type='text/html', charset='UTF-8')
    elif (format == 'excel'):
        b= BytesIO()
        pd.ExcelWriter(b)
        getDataframe().to_excel(b)
        r = Response(b.getvalue(), content_type='application/force-download', content_disposition='attachment; filename=data.xls')

    else:
        r = Response('Bad paramters ' + str(request.params), content_type='text/html', charset='UTF-8')

    return r

#



#







@view_config(route_name='forecast')
def forecastServer(request):




    format = getParamterOrdefault(request.params, 'format', 'default', ['html', 'json', 'xml', 'serialized', 'csv', 'excel'])
    days = getIntParameter(request.params, 'days', -1, range(20, 301))

    if days == -1 or format=='default':
        r = Response('Bad paramters ' + str(request.params), content_type='text/html', charset='UTF-8')
    else:

        if (format=='csv'):
            _ , df = getForecastData(days)
            s = StringIO()
            df.to_csv(s)
            r = Response(s.getvalue(), content_type='text/plain', charset='UTF-8')
        elif (format == 'html'):
            _ , df =  getForecastData(days)
            s = StringIO()
            df.to_html(s, index=True)
            r = Response(s.getvalue(), content_type='text/html', charset='UTF-8')
        elif (format=='xml'):
            _ , df = getForecastData(days)
            root = et.Element('root')

            for i, row in df.iterrows():
                data = et.SubElement(root, 'row')
                data.set('iter', str(i))
                for head in df.columns:
                    aux = et.SubElement(data, head)
                    aux.text = str(row[head])

            r = Response(et.tostring(root), content_type='text/xml', charset='UTF-8')
        elif (format=='json'):
            _ , df = getForecastData(days)
            s = StringIO()
            df.to_json(s)
            r = Response(s.getvalue(), content_type='text/plain', charset='UTF-8')
        elif (format == 'serialized'):
            _, df = getForecastData(days)
            r = Response(base64.encodebytes(pkl.dumps(df)).decode('utf-8'), content_type='text/html',
                         charset='UTF-8')

        elif (format == 'excel'):
            b= BytesIO()
            pd.ExcelWriter(b)
            _, df = getForecastData(days)
            df.to_excel(b)
            r = Response(b.getvalue(), content_type='application/force-download', content_disposition='attachment; filename=data.xls')




    return r

#





#


@view_config(route_name='charts')
def chartServer(request):
    format = getParamterOrdefault(request.params, 'format', 'not',
                                  ['png', 'jpg'])

    chartType = getParamterOrdefault(request.params, 'chart', 'not',
                                  ['data', 'components','forecast'])

    dpi = getIntParameter(request.params, 'dpi', -1, range(20, 301))

    days = getIntParameter(request.params, 'days', -1, range(20, 301))


    if dpi==-1 or chartType=='not' or format=='not' or days==-1:
        return  Response('Bad paramters '+str(request.params), content_type='text/html', charset='UTF-8')


    else:
        if chartType=='data':



            df = getFilteredDataframe()
            plt.clf()
            img = plt.imread('matplotlib.png')
            plt.plot(df.date,df.mx_usd, 'r')
            fig = plt.gcf()
            fig.set_size_inches(18.5, 10.5)
            plt.title('USD MXP');
            ax = plt.axes([.60, -0.13, 0.25, 0.8], frameon=True)

            ax.imshow(img, alpha=0.112)
            ax.axis('off')
            figure = BytesIO()
            print('DATA')
            plt.savefig(figure, format=format,dpi=dpi)

        elif chartType=='components':
            prophet , df = getForecastData(days)
            prophet.plot_components(df)

            fig = plt.gcf()
            fig.set_size_inches(18.5, 10.5)
            img = plt.imread('matplotlib.png')


            plt.title('USD MXP');
            ax = plt.axes([.60, -0.13, 0.25, 0.8], frameon=True)

            ax.imshow(img, alpha=0.112)
            ax.axis('off')
            figure = BytesIO()
            plt.savefig(figure, format=format, dpi=dpi)
        elif chartType == 'forecast':
            prophet, forecast = getForecastData(days)

            img = plt.imread('matplotlib.png')
            fig = plt.figure(figsize=(10, 6))
            AX = fig.add_subplot(111)

            y_low = max(forecast['yhat_lower'])
            y_max = max(forecast['yhat_upper'])
            y_trend = max(forecast['yhat'])

            y_low_color = '#014c00AF'
            y_max_color = '#FF4432AF'
            y_trend_color = '#11c3f4AF'

            index = np.argmax(forecast['yhat'], max(forecast['yhat']))

            date = forecast.loc[index]['ds'].strftime("%d/%m/%Y")

            prophet.plot(forecast, xlabel='Date', ylabel='PESOS', ax=AX)

            AX.axhline(y_low, color=y_low_color, linestyle='-')
            AX.axhline(y_max, color=y_max_color, linestyle='-')
            AX.axhline(y_trend, color=y_trend_color, linestyle='-')

            AX.annotate('Min forecast:  ' + ('{0:.3f}'.format(y_low)), xy=(forecast['ds'][2000], y_low),
                        xytext=(forecast['ds'][1900], y_low - 3), fontsize=15, color=y_low_color,
                        arrowprops=dict(facecolor='black', shrink=0.0095, alpha=0.3))

            AX.annotate('Max forecast:  ' + ('{0:.3f}'.format(y_max)), xy=(forecast['ds'][800], y_max),
                        xytext=(forecast['ds'][700], y_max - 3), fontsize=15, color=y_max_color,
                        arrowprops=dict(facecolor='black', shrink=0.0095, alpha=0.3))

            AX.annotate('trend forecast:  ' + ('{0:.3f}'.format(y_trend)), xy=(forecast['ds'][3800], y_trend),
                        xytext=(forecast['ds'][3700], y_trend - 3), fontsize=15, color=y_trend_color,
                        arrowprops=dict(facecolor='black', shrink=0.0095, alpha=0.3))

            plt.text(forecast['ds'][2000], -.65, 'forecasting for   ' + date, style='italic', fontsize=12,
                     bbox={'facecolor': 'blue', 'alpha': 0.1, 'pad': 10})

            plt.text(forecast['ds'][4800], -.65,
                     'Build by: Greg flores @:' + datetime.datetime.now().strftime("%d-%m-%Y %H:%M"), style='italic',
                     fontsize=12,
                     bbox={'facecolor': y_trend_color, 'alpha': 0.2, 'pad': 10})

            fig = plt.gcf()

            fig.set_size_inches(18.5, 10.5)

            plt.title('USD MXP');
            ax = plt.axes([.70, -0.23, 0.25, 0.8], frameon=True)

            ax.imshow(img, alpha=0.162)
            ax.axis('off')
            figure = BytesIO()

            plt.savefig(figure, format=format, dpi=dpi)

    if format=='png':
        content_type = "image/png"
    else:
        content_type = "image/jpg"



    return Response(body = figure.getvalue(),content_type=content_type)


#


#
@view_config(route_name='qrbuilder')
def qrServer(request):
    scale = getIntParameter(request.params, 'scale', -1, range(2, 11))
    if scale== -1:
        return Response('Bad paramters ' + str(request.params), content_type='text/html', charset='UTF-8')
    else:

        oRet = BytesIO()
        oQR  = pyqrcode.create('http://'+socket.gethostbyname(socket.gethostname())+':8080/app/welcome')

        oQR.png(oRet, scale=scale)
        r =  Response(body = oRet.getvalue(), content_type="image/png")
        return r




#

#

@view_config(context=Exception,  renderer='error.jinja2')
def error(context, request):
    fp = StringIO()
    traceback.print_exc(file=fp)

    return {'error':fp.getvalue(),'favicon':'logo.png'}


#


#


@view_config(context=HTTPNotFound, renderer='404.jinja2')
def not_found(context, request):
    request.response.status = 404
    return {}




def quitting():
    print('Quitting......')
    quit(-1)

#



#

def validateParameters(args):


    if not os.path.isfile(args['csv_file']):
        print('File:',colored((args['csv_file']),'red'),'not found please verify.')
        quitting()
    elif not os.access(args['csv_file'], os.R_OK):
        print('File:', colored((args['csv_file']), 'red'), 'can not be read')
        quitting()


#


#

if __name__ == '__main__':

    ap = argparse.ArgumentParser(description='WEB SERVICE SERVER',
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    ap.add_argument('-csv_file', required=True, help='file with time series dataframe with csv format ', type=str)
    args = vars(ap.parse_args())
    validateParameters(args)

    os.system('clear')



    W.printWelcome()
    print('*'*40)
    print(W.printLibsVersion(['pyramid','numpy','openpyxl','pandas','matplotlib','fbprophet','datetime','setuptools','py-common-fetch','argparse','pyqrcode']))
    with Configurator() as config:

        config.include('pyramid_jinja2')

        config.add_route('entry', '/')
        config.add_route('hello', '/app/welcome')
        config.add_route('dataset', '/app/dataset')
        config.add_route('forecast', '/app/forecast')
        config.add_route('charts', '/app/charts')
        config.add_route('qrbuilder', '/app/qrbuilder')



        config.add_static_view(name='app/static/', path='static/')

        print(__file__)
        config.scan('__main__')
        app = config.make_wsgi_app()
        print('running sevrer:',port)
        server = make_server('0.0.0.0', port, app)
        server.serve_forever()


