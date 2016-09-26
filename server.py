from bottle import route, run, template, static_file, request
import os
import json

views_path = os.path.join(os.getcwd(), 'views')
static_path = os.path.join(os.getcwd(), 'static')

@route('/')
def go_to_index():
    return template('index.html', lookup=views_path)

@route('/upload', method='POST')
def do_upload():
    upload = request.files.get('upload')
    name, ext = os.path.splitext(upload.filename)
    import sopa
    contenido = str(upload.file.read())
    resultado = sopa.procesar(contenido)
    return template('reporte.html', reportes=resultado.reportes)
    
@route('/plotly')
def go_to_plotly():
    trace1 = {}
    trace1['name'] = 'serie 1'
    trace1['x'] = [0, 1, 2]
    trace1['y'] = [6, 10, 2]
    trace1['error_y'] = {}
    trace1['error_y']['type'] = 'data'
    trace1['error_y']['array'] = [1, 2, 3]
    trace1['error_y']['visible'] = True
    trace1['type'] = 'scatter'
    
    trace2 = {}
    trace1['name'] = 'serie 2'
    trace2['x'] = [0, 1, 2]
    trace2['y'] = [8, 5, 4]
    trace2['error_y'] = {'type': 'data', 'visible': True, 'array': [3, 2, 1]}
    trace2['type'] = 'scatter'    
    
    layout = {}    
    layout['xaxis'] = {'title': 'leyenda eje x'}
    layout['yaxis'] = {'title': 'leyenda eje y'}
    layout['margin'] = {'t': 20}
    layout['hovermode'] = 'closest'
    
    layout['showlegend'] = True  
    legend = {}    
    legend['x'] = 100
    legend['y'] = 1
    legend['traceorder'] = 'normal'
    legend['font'] = {'family': 'sans-serif', 'size': 12, 'color': '#000'}
    legend['bgcolor'] = '#E2E2E2',
    legend['bordercolor'] = '#FFFFFF',
    legend['borderwidth'] = 2  
    layout['legend'] = legend
    
    return {'data':[trace1, trace2], 'layout':layout}

@route('/static/<filename:path>')
def send_static(filename):
    return static_file(filename, root=static_path)

run(host='localhost', port=8000, debug=True, reloader=True)
