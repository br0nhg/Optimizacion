from geopy.distance import geodesic
from .estaciones import ESTACIONES_BOMBEROS
from .comunas import COMUNAS

# Definición de conjuntos según nuevo modelo
I = range(1, 37)  # 36 comunas (continentales)
J = range(1, 41)  # 40 estaciones
T = range(0, 24)  # 24 horas

# Constantes operativas
C_MAX = 4  # Capacidad máxima de bomberos por carro

def calcular_distancia(coord1, coord2):
    """Calcula distancia en km entre dos coordenadas"""
    try:
        return geodesic(coord1, coord2).kilometers
    except Exception as e:
        print(f"Error calculando distancia: {e}")
        return float('inf')

def generar_parametros():
    """Genera todos los parámetros necesarios para el modelo"""
    try:
        params = {}
        
        # Dit: Demanda de bomberos en la zona i en el tiempo t
        params['Dit'] = {
            (i,t): max(1, COMUNAS[list(COMUNAS.keys())[i-1]]['poblacion'] // 10000)
            for i in I for t in T
        }
        
        # Ej: Total de bomberos de la estación j
        params['Ej'] = {
            j: ESTACIONES_BOMBEROS[list(ESTACIONES_BOMBEROS.keys())[j-1]]['capacidad_bomberos']
            for j in J
        }
        
        # Fj: Cantidad total de carros en la estación j
        params['Fj'] = {
            j: ESTACIONES_BOMBEROS[list(ESTACIONES_BOMBEROS.keys())[j-1]]['capacidad_carros']
            for j in J
        }
        
        # Tijt: Tiempo de trayecto
        params['Tijt'] = {}
        for i in I:
            comuna = list(COMUNAS.keys())[i-1]
            coord_comuna = COMUNAS[comuna]['coords']
            for j in J:
                estacion = list(ESTACIONES_BOMBEROS.keys())[j-1]
                coord_estacion = ESTACIONES_BOMBEROS[estacion]['coords']
                base_time = calcular_distancia(coord_comuna, coord_estacion)
                for t in T:
                    # Ajuste por hora del día
                    if t < 5:  # Madrugada
                        params['Tijt'][i,j,t] = base_time * 0.7  # Menos tráfico
                    elif 6 <= t < 17:  # Día normal
                        params['Tijt'][i,j,t] = base_time
                    else:  # Hora punta
                        params['Tijt'][i,j,t] = base_time * 1.5  # Más tráfico
        
        # Rjt: Tiempo de preparación
        params['Rjt'] = {
            (j,t): 2 if 6 <= t < 17 else 3.5 if t < 5 else 3
            for j in J for t in T
        }
        
        # TMit: Tiempo máximo permitido de respuesta
        params['TMit'] = {
            (i,t): 20 if COMUNAS[list(COMUNAS.keys())[i-1]]['tipo_zona'] == 'urbana' else 30
            for i in I for t in T
        }
        
        # Pit: Prioridad de la zona (valor entre 1 y 100)
        params['Pit'] = {
            (i,t): COMUNAS[list(COMUNAS.keys())[i-1]]['prioridad_base']
            for i in I for t in T
        }
        
        # tau: Tiempo de operación (ahora como diccionario de dos índices)
        params['tau'] = {
            (i,t): max(1, int(0.24 * params['Pit'][i,t]))  # Aseguramos que sea entero y mínimo 1
            for i in I for t in T
        }
        
        # Cmax: Capacidad máxima de bomberos por carro
        params['Cmax'] = C_MAX
        
        return params

    except Exception as e:
        print(f"Error generando parámetros: {e}")
        raise
    
def verificar_parametros(params):
    """Verifica que los parámetros sean factibles"""
    try:
        # Verificar que hay suficientes bomberos para la demanda
        total_bomberos = sum(params['Ej'].values())
        max_demanda = max(params['Dit'].values())
        print(f"Total bomberos disponibles: {total_bomberos}")
        print(f"Máxima demanda en un período: {max_demanda}")
        
        # Verificar que hay suficientes carros
        total_carros = sum(params['Fj'].values())
        max_demanda_carros = max(params['Dit'].values()) / params['Cmax']
        print(f"Total carros disponibles: {total_carros}")
        print(f"Máxima demanda de carros: {max_demanda_carros}")
        
        # Verificar tiempos
        print("\nRango de tiempos de trayecto:", 
              min(params['Tijt'].values()), "-", 
              max(params['Tijt'].values()))
        
        print("Rango de tiempos máximos:", 
              min(params['TMit'].values()), "-", 
              max(params['TMit'].values()))
        
        return True
    except Exception as e:
        print(f"Error en verificación de parámetros: {e}")
        return False

# Llamar a la verificación después de generar parámetros
params = generar_parametros()
verificar_parametros(params)