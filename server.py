from bottle import route, run, template, static_file, request
import os
import math
import json
import sopa

views_path = os.path.join(os.getcwd(), 'views')
static_path = os.path.join(os.getcwd(), 'static')

@route('/')
def go_to_index():
    return template('index.html', lookup=views_path)

def get_firmas_espectrales(reportes):
    firmas = []
    for reporte in reportes:
        firma = {}
        firma['name'] = reporte.titulo
        firma['x'] = reporte.lambdas
        firma['y'] = [banda.media for banda in reporte.bandas]
        firma['error_y'] = {}
        firma['error_y']['type'] = 'data'
        firma['error_y']['array'] = [math.sqrt(banda.varianza) for banda in reporte.bandas]
        firma['error_y']['visible'] = True
        firma['type'] = 'scatter'
        firmas.append(firma)
    return firmas

def get_histogramas(reportes):
    histogramas = []
    for reporte in reportes:
        for banda in sorted(reporte.histogramas):
          histo = {}
          histo['x'] = [x for x,y in reporte.histogramas[banda]]
          histo['y'] = [y for x,y in reporte.histogramas[banda]]          
          histo['name'] = banda
          histo['type'] = 'histogram'
          histo['opacity'] = 0.75 
          histogramas.append(histo)
    return histogramas

@route('/upload', method='POST')
def do_upload():
    lambdas = request.forms.get('lambdas')
    upload = request.files.get('upload')
    name, ext = os.path.splitext(upload.filename)
    contenido = str(upload.file.read())    
    reportes = sopa.procesar(contenido, sopa.lambdas_sensor('landsat8'))
    firmas = get_firmas_espectrales(reportes)
    histos = get_histogramas(reportes)
    return template('reporte.html', reportes=reportes, firmas_espectrales=json.dumps(firmas), histogramas=json.dumps(histos))

@route('/static/<filename:path>')
def send_static(filename):
    return static_file(filename, root=static_path)

run(host='localhost', port=8000, debug=True, reloader=True)