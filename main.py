import logging
import sys
from gurobipy import GRB
from data.parametros import generar_parametros, I, J, T
from data.estaciones import validar_estaciones
from data.comunas import validar_comunas
from model.optimizacion import crear_modelo_optimizacion
from model.validacion import validar_solucion, generar_reporte

# Configuración del logging más detallada
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    """
    Función principal que ejecuta todo el proceso de optimización
    """
    try:
        print("\n=== INICIANDO PROCESO DE OPTIMIZACIÓN ===\n")
        
        # 1. Validar datos de entrada
        print("1. Validando datos de entrada...")
        if not validar_estaciones():
            print("Error: Validación de estaciones fallida")
            return
        if not validar_comunas():
            print("Error: Validación de comunas fallida")
            return
        print("✓ Validación de datos completada\n")

        # 2. Generar parámetros
        print("2. Generando parámetros del modelo...")
        params = generar_parametros()
        print("✓ Parámetros generados exitosamente")
        print(f"   - Número de comunas: {len(I)}")
        print(f"   - Número de estaciones: {len(J)}")
        print(f"   - Períodos de tiempo: {len(T)}\n")

        # 3. Crear modelo
        print("3. Creando modelo de optimización...")
        m, X, Y, Z, EE, FF, V, U = crear_modelo_optimizacion(params, I, J, T)
        print("✓ Modelo creado exitosamente")
        print(f"   - Número de variables: {m.NumVars}")
        print(f"   - Número de restricciones: {m.NumConstrs}\n")

        # 4. Optimizar
        print("4. Iniciando proceso de optimización...")
        m.setParam('OutputFlag', 1)  # Mostrar proceso de optimización
        m.optimize()

        # 5. Procesar resultados
        print("\n5. Procesando resultados...")
        if m.status == GRB.OPTIMAL:
            print("✓ Solución óptima encontrada!")
            print(f"   Valor objetivo: {m.objVal:.2f}")
            
            # 6. Validar solución
            print("\n6. Validando solución...")
            if validar_solucion(X, Y, Z, V, U, params, I, J, T):
                print("✓ Solución válida")
                
                # 7. Mostrar resultados detallados
                print("\n=== RESULTADOS DETALLADOS ===")
                
                # Total de recursos utilizados
                total_bomberos = sum(X[i,j,t].X for i in I for j in J for t in T)
                total_carros = sum(Y[i,j,t].X for i in I for j in J for t in T)
                print(f"\nRecursos totales utilizados:")
                print(f"- Bomberos desplegados: {total_bomberos}")
                print(f"- Carros utilizados: {total_carros}")
                
                # Mostrar asignaciones por período
                print("\nAsignaciones por período:")
                for t in T:
                    bomberos_t = sum(X[i,j,t].X for i in I for j in J)
                    carros_t = sum(Y[i,j,t].X for i in I for j in J)
                    if bomberos_t > 0 or carros_t > 0:
                        print(f"\nPeríodo {t}:")
                        print(f"- Bomberos activos: {bomberos_t}")
                        print(f"- Carros activos: {carros_t}")
                        
                        # Mostrar asignaciones específicas
                        for i in I:
                            for j in J:
                                if X[i,j,t].X > 0:
                                    print(f"  Comuna {i} <- Estación {j}:")
                                    print(f"    Bomberos: {int(X[i,j,t].X)}")
                                    print(f"    Carros: {int(Y[i,j,t].X)}")
                
                # 8. Guardar resultados
                print("\n7. Guardando resultados...")
                guardar_resultados(m, X, Y, Z, V, U, params)
                print("✓ Resultados guardados exitosamente")
                
            else:
                print("✗ Error: La solución no es válida")
        else:
            print("\n✗ Error: No se encontró solución óptima")
            if m.status == GRB.INFEASIBLE:
                print("El modelo es infactible")
            elif m.status == GRB.UNBOUNDED:
                print("El modelo es no acotado")
            else:
                print(f"Estado del modelo: {m.status}")

    except Exception as e:
        print(f"\n✗ Error en la ejecución: {str(e)}")
        raise

    print("\n=== PROCESO COMPLETADO ===\n")

def guardar_resultados(m, X, Y, Z, V, U, params):
    """
    Guarda los resultados en archivos
    """
    try:
        # Crear directorio si no existe
        import os
        if not os.path.exists('resultados'):
            os.makedirs('resultados')

        # Guardar valor objetivo
        with open('resultados/objetivo.txt', 'w') as f:
            f.write(f"Valor objetivo: {m.objVal:.2f}\n")

        # Guardar asignaciones
        with open('resultados/asignaciones.csv', 'w') as f:
            f.write("Tiempo,Comuna,Estacion,Bomberos,Carros,Tiempo_Respuesta\n")
            for t in T:
                for i in I:
                    for j in J:
                        if X[i,j,t].X > 0:
                            tiempo_resp = params['Tijt'][i,j,t] + params['Rjt'][j,t]
                            f.write(f"{t},{i},{j},{int(X[i,j,t].X)},{int(Y[i,j,t].X)},{tiempo_resp:.2f}\n")

    except Exception as e:
        print(f"Error guardando resultados: {e}")
        raise

if __name__ == "__main__":
    main()