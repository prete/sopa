from lxml import etree
import numpy as np
import matplotlib.pyplot as plt
import os.path
import getopt
import sys
import hashlib

class banda(object):
    def __init__(self):
        self.nombre = ''
        self.media = 0.0
        self.varianza = 0.0
        self.minimo = 0.0
        self.maximo = 0.0
        self.histograma = {}
    def __str__(self):
        return 'Banda: {} - Media: {} - Varianza: {} - Minimo: {} - Maximo: {}'.format(self.nombre, self.media, self.varianza, self.minimo, self.maximo)
    def __repr__(self):
        return self.__str__()

class banda_valor(object):
    def __init__(self, banda, valor):
        self.banda = banda
        self.valor = valor
    def __str__(self):
        return '{}={}'.format(self.banda, self.valor)
    def __repr__(self):
        return self.__str__()

class matriz_bandas(object):
    def __init__(self, matriz, bandas):
        self.matriz = matriz
        self.bandas = bandas

'''
class coleccion_reportes(object):
    def __init__(self, reportes):
        self.reportes = reportes
    def plot_medias(self, longitudes_onda, xlabel, ylabel, title):
        ymin = 10000000
        ymax = 0
        for r in self.reportes:
            medias = r.medias()
            ymin = min([min(medias),ymin])
            ymax = max([max(medias),ymax])
            plt.plot(longitudes_onda, medias, linestyle = "-",color=r.color(), marker = "o", label=r.titulo)
        plt.legend(bbox_to_anchor=(1.1, 1), loc=2)
        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.xlim(min(longitudes_onda),max(longitudes_onda))
        plt.ylim(ymin, ymax)
        plt.show()
'''
def color_hash(txt):    
    hexcolor = hashlib.md5(txt.encode('ascii')).hexdigest()
    return '#'+hexcolor[8:10]+hexcolor[18:19]+hexcolor[27:30]

class reporte(object):
    def __init__(self):
        self.titulo = ''
        self.bandas = []
        self.histogramas = []
        self.lambdas = []
        self.autovalores = {}
        self.matriz_correlacion = matriz_bandas(np.matrix([]),[])
        self.matriz_covarianza = matriz_bandas(np.matrix([]),[])
    def color(self):
        return color_hash(self.titulo)

def procesar(contenido, longitudes_onda):
    reportes_resultado = []
    html = contenido.replace('\n', '').replace('<html>','').split('</html>')    
    html = [bloque for bloque in html if len(bloque)>1]
    if html is None or len(html)==0:
        print('No se pudo cargar el reporte.')
        return

    for sub_html in html :
        element = etree.fromstring('<html>'+sub_html+'</html>')
        titulo = element.xpath('.//em[text()="Resultado"]/preceding::h1/font')
        repo = reporte()
        if len(titulo)!=0:
            repo.titulo = titulo[0].text
        else:
            repo.titulo = 'Serie #{}'.format(len(reportes_resultado)+1)

        resultados = element.xpath('.//em[text()="Resultado"]/ancestor::font/table/tr')
        for resultado in resultados:
            repo.lambdas = longitudes_onda
            repo.bandas = parse_parametros_basicos(resultado)
            repo.autovalores = parse_autovalores(resultado)
            print(repo.autovalores)
            #repo.matriz_correlacion = parse_matriz_correlacion(resultado)
            #repo.matriz_covarianza = parse_matriz_covarianza(resultado)
            repo.histogramas = parse_histogramas(resultado)
        reportes_resultado.append(repo)
    return reportes_resultado

#Parametros basicos
def parse_parametros_basicos(resultado):
    bandas = {}
    parametros_basicos = resultado.xpath('.//font[text()="Parametros basicos"]/ancestor::tr/following-sibling::*/td/table')
    if len(parametros_basicos)!=0:
        parametros_basicos = parametros_basicos[0]
        for f,fila in enumerate(parametros_basicos):
            for c,celda in enumerate(fila):
                if f==0 or c==0:
                    continue
                nombre_banda = parametros_basicos[0][c].text
                if nombre_banda not in bandas:
                    bandas[nombre_banda] = banda()
                    bandas[nombre_banda].nombre = nombre_banda
                if f==1:
                    bandas[nombre_banda].media = float(celda.text)
                elif f==2:
                    bandas[nombre_banda].varianza = float(celda.text)
                elif f==3:
                    bandas[nombre_banda].minimo = float(celda.text)
                elif f==4:
                    bandas[nombre_banda].maximo = float(celda.text)
    return sorted(bandas.values(), key=lambda b: b.nombre)

#Matriz de correlacion
def parse_matriz_correlacion(resultado):
    matriz_resultado = []
    matriz_correlacion = resultado.xpath('.//font[text()="Matriz de correlacion"]/ancestor::tr/following-sibling::*/td/table')
    if len(matriz_correlacion)!=0:
        matriz_correlacion = matriz_correlacion[0]
        for fila in matriz_correlacion[1:]:
            items = []
            for celda in fila[1:]:
                items.append(float(celda.text))
            matriz_resultado.append(items)
    return matriz_bandas(np.matrix(matriz_resultado), [col.text for col in matriz_correlacion[0][1:]])

#Matriz de covarianza
def parse_matriz_covarianza(resultado):
    matriz_resultado = []
    matriz_covarianza = resultado.xpath('.//font[text()="Matriz de covarianza"]/ancestor::tr/following-sibling::*/td/table')
    if len(matriz_covarianza)!=0:
        matriz_covarianza = matriz_covarianza[0]
        for fila in matriz_covarianza[1:]:
            items = []
            for celda in fila[1:]:
                items.append(float(celda.text))
            matriz_resultado.append(items)
    return matriz_bandas(np.matrix(matriz_resultado), [col.text for col in matriz_covarianza[0][1:]])

#Histogramas
def parse_histogramas(resultado):
    histogramas_resultado = {}
    histogramas = resultado.xpath('.//font[text()="Histogramas"]/ancestor::h1/following-sibling::table/tr/td')
    if len(histogramas)!=0:
        for histograma in histogramas:
            banda = histograma.xpath('.//table/tr/td/table/tr/td/h1/font')[0].text
            histogramas_resultado[banda] = {}
            histograma = histograma.xpath('./table/tr/td/table/tr/td/table')
            if len(histograma)!=0:
                histograma = histograma[0]
                histogramas_resultado[banda] = [(float(fila[0].text), float(fila[1].text)) for fila in histograma[1:]]
    return histogramas_resultado

#Autovalores
def parse_autovalores(resultado):
    autovalores_resultado = {}
    autovalores = resultado.xpath('.//font[contains(., "Autovalores")]/ancestor::tr/following-sibling::*/td/table')
    if len(autovalores)!=0:
        autovalores = autovalores[0]
        for i in range(1,len(autovalores[0])):
            autovalores_resultado[autovalores[0][i].text] = float(autovalores[1][i].text)    
    return autovalores_resultado

#Longitud de onda de las bandas que capta el sensor
def lambdas_sensor(sensor):
   lambdas = {}   
   lambdas["landsat8"] = [482, 562, 655, 865, 1610, 2200]   
   lambdas["spot5"] = [545, 645, 840, 1665]
   return lambdas[sensor]
   
def plot_medias(reportes, xlabel, ylabel, title):
    ymin = 10000000
    ymax = 0
    for r in reportes:
        medias = r.medias()
        xmin = min([min(r.lambdas),xmin])
        xmax = max([max(r.lambdas),xmax])
        ymin = min([min(medias),ymin])
        ymax = max([max(medias),ymax])
        plt.plot(r.lambdas, medias, linestyle = "-",color=r.color(), marker = "o", label=r.titulo)
    plt.legend(bbox_to_anchor=(1.1, 1), loc=2)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.xlim(xmin, xmax)
    plt.ylim(ymin, ymax)
    plt.show()

############################################################################### 

def usage():
   print("SOPA - SoPI Parser")
   print("Herramientas de Python3 para el procesamiento de reportes de SoPI")
   print("")
   print("uso: sopa.py -r reporte-htm -s landsat8")
   print("")
   print("      -s/--sensor:    especifica qué sensor se utilizó para generar el reporte.")
   print("                      ejemplo: sopa.py -r reporte.htm -s landsat8")
   print("      -l/--lambdas:   especifica las longitudes de onda de las bandas del sensor.")
   print("                      ejemplo: sopa.py -r reporte.html -l landsat8 482,561,655,864,1608,2200")
   print("")

#punto de entrada de la linea de comandos
if __name__ == "__main__":
   if not len(sys.argv[1:]):
      usage()
      exit(0)

    # leo las opciones de la linea de comandos
   try:
      opts, args = getopt.getopt(sys.argv[1:],"hr:b:s:l:p:s:", ["help","reporte","sensor","lambdas","bandas","proceso","salida"])
   except getopt.GetoptError as err:
      print(str(err))
      usage()
      exit(0)

   for o,a in opts:
      #Muestro el help de la herramienta
      if o in ("-h","--help"):
          usage()
          exit(0)

      #Verifico que la ruta del archivo del reporte sea válida
      elif o in ("-r","--reporte"):
         ruta_reporte = a
         try:
            if not os.path.isfile(ruta_reporte):
               print('No se pudo cargar el reporte. Verifique la ruta del archivo.')
               exit(0)
         except NameError:
            print('No se especificó la ruta del reporte.')
            exit(0)

      #Si se especificó el sensor, busco las longitudes de onda para sus bandas.
      elif o in ("-s","--sensor"):
         sensor = a
         try:
            print('Procesando para sensor: ', sensor)
            lambdas = lambdas_sensor(sensor)
         except NameError:
            print('No se especificó el sensor.')
            print('Ejemplo para Landsat 8: landsat8')
            exit(0)
         except KeyError:
            print('El sensor ' , sensor , ' no existe en la base de datos. Pruebe especificar los lamdas manualmente con la opción -l/--lambdas')
            print('Ejemplo para Landsat 8: landsat8')
            exit(0)

      #Si se especificaron las longitudes de onda manualmente
      elif o in ("-l","--lambdas"):
         lambdas = a
         try:
            lambdas = [ int(x) for x in lambdas.split(',') ]
         except NameError:
            print('No se especificaron las longitudes de ondas a utilizar.')
            print('Ejemplo para landsat8: 482,561,655,864,1608,2200')
            exit(0)
         except ValueError:
            print('Formato incorrecto de longitudes de onda.')
            print('Ejemplo para landsat8: 482,561,655,864,1608,2200')
            exit(0)

      #Si se especificaron las bandas a procesar
      elif o in ("-b","--bandas"):
         bandas = a

      else:
          assert False,"Unhandled Option"

   with open(ruta_reporte) as archivo:
      contenido = archivo.read()
      reportes = procesar(contenido, lambdas)
      #plot_medias(reportes, "Longitud de londa [nm]", "Relectancia [Arb.]", "Firmas espectrales")