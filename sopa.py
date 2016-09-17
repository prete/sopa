from lxml import etree
import numpy as np
import matplotlib.pyplot as plt

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

class reporte(object):
    def __init__(self):
        self.titulo = ''
        self.bandas = []
        self.histogramas = []
        self.matriz_correlacion = matriz_bandas(np.matrix([]),[])
        self.matriz_covarianza = matriz_bandas(np.matrix([]),[])
    def medias(self):
        return [b.media for b in self.bandas]        
    def medias_segun_banda(self):
        return [banda_valor(b.nombre, b.media) for b in self.bandas]
    def varianzas_segun_banda(self):
        return [banda_valor(b.nombre, b.varianza) for b in self.bandas]
    def varianzas(self):
        return [b.varianza for b in self.bandas]        
    def minimos_segun_banda(self):
        return [banda_valor(b.nombre, b.minimo) for b in self.bandas]
    def minimos(self):
        return [b.minimo for b in self.bandas]
    def maximos_segun_banda(self):
        return [banda_valor(b.nombre, b.maximo) for b in self.bandas]
    def maximos(self):
        return [b.maximo for b in self.bandas]
    def color(self):
        import hashlib
        hexcolor = hashlib.md5(self.titulo.encode('ascii')).hexdigest()
        return '#'+hexcolor[8:10]+hexcolor[18:20]+hexcolor[28:30]
        #colors = ['#1b9e77','#d95f02','#7570b3','#e7298a','#66a61e','#e6ab02']
        #return colors[hash(self.titulo)%6]

def procesar(contenido):
    reportes_resultado = []
    html = contenido.replace('\n', '').replace('<html>','').split('</html>')
    html = [bloque for bloque in html if len(bloque)!=0]
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
            repo.bandas = parse_parametros_basicos(resultado)
            repo.matriz_correlacion = parse_matriz_correlacion(resultado)
            repo.matriz_covarianza = parse_matriz_covarianza(resultado)            
            repo.histogramas = parse_histogramas(resultado)        
        reportes_resultado.append(repo)
    return coleccion_reportes(reportes_resultado)
    
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
            banda = histograma.xpath('.//table/tr/td/table/tr/td/h1/font/text()')[0]
            histogramas_resultado[banda] = {}
            histograma = histograma.xpath('./table/tr/td/table/tr/td/table')
            if len(histograma)!=0:
                histograma = histograma[0]
                for fila in histograma[1:]:
                    histogramas_resultado[banda][float(fila[0].text)] = float(fila[1].text)
    return sorted(histogramas_resultado)