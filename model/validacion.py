from gurobipy import GRB
import logging

logger = logging.getLogger(__name__)

def validar_solucion(X, Y, Z, V, U, params, I, J, T):
    """
    Valida que la solución cumpla con todas las restricciones del nuevo modelo
    
    Args:
        X, Y, Z, V, U: Variables de decisión del modelo
        params: Diccionario con los parámetros
        I, J, T: Conjuntos del modelo
    Returns:
        bool: True si la solución es válida
    """
    try:
        # Validar demanda
        for i in I:
            for t in T:
                bomberos_asignados = sum(X[i,j,t].X for j in J)
                assert bomberos_asignados >= params['Dit'][i,t], \
                    f"Demanda no satisfecha en zona {i}, tiempo {t}"

        # Validar capacidad de bomberos
        for j in J:
            for t in T:
                bomberos_usados = sum(X[i,j,t].X for i in I)
                assert bomberos_usados <= params['Ej'][j], \
                    f"Capacidad de bomberos excedida en estación {j}, tiempo {t}"

        # Validar capacidad de carros
        for j in J:
            for t in T:
                carros_usados = sum(Y[i,j,t].X for i in I)
                assert carros_usados <= params['Fj'][j], \
                    f"Capacidad de carros excedida en estación {j}, tiempo {t}"

        # Validar relación bomberos-carros
        for i in I:
            for j in J:
                for t in T:
                    if Y[i,j,t].X > 0:
                        assert X[i,j,t].X <= params['Cmax'] * Y[i,j,t].X, \
                            f"Capacidad de carro excedida en ruta {i}-{j} tiempo {t}"

        # Validar tiempo de respuesta
        for i in I:
            for j in J:
                for t in T:
                    if Z[i,j,t].X > 0.5:
                        tiempo_total = params['Tijt'][i,j,t] + params['Rjt'][j,t]
                        assert tiempo_total <= params['TMit'][i,t], \
                            f"Tiempo máximo excedido para zona {i} desde estación {j} en tiempo {t}"

        logger.info("Todas las validaciones pasaron correctamente")
        return True

    except AssertionError as e:
        logger.error(f"Validación fallida: {e}")
        return False

def generar_reporte(m, X, Y, Z, V, U, params, I, J, T):
    """
    Genera un reporte detallado de la solución
    """
    if m.status == GRB.OPTIMAL:
        print("\n" + "="*50)
        print("RESULTADOS DE LA OPTIMIZACIÓN")
        print("="*50)
        
        # Valor objetivo
        print(f"\nValor objetivo (tiempo total ponderado): {m.objVal:.2f} minutos")
        
        # Recursos totales
        total_bomberos = sum(X[i,j,t].X for i in I for j in J for t in T)
        total_carros = sum(Y[i,j,t].X for i in I for j in J for t in T)
        
        print("\nRECURSOS TOTALES UTILIZADOS:")
        print(f"- Bomberos desplegados: {total_bomberos}")
        print(f"- Carros utilizados: {total_carros}")
        
        # Análisis por hora
        print("\nANÁLISIS POR HORA:")
        for t in T:
            bomberos_hora = sum(X[i,j,t].X for i in I for j in J)
            carros_hora = sum(Y[i,j,t].X for i in I for j in J)
            if bomberos_hora > 0 or carros_hora > 0:
                print(f"\nHora {t}:")
                print(f"- Bomberos activos: {bomberos_hora}")
                print(f"- Carros activos: {carros_hora}")
        
        # Análisis por estación
        print("\nANÁLISIS POR ESTACIÓN:")
        for j in J:
            total_salidas = sum(Z[i,j,t].X for i in I for t in T)
            if total_salidas > 0:
                print(f"\nEstación {j}:")
                print(f"- Total salidas: {total_salidas}")
                print(f"- Bomberos retornados: {sum(V[j,t].X for t in T)}")
                print(f"- Carros retornados: {sum(U[j,t].X for t in T)}")
        
        # Tiempos de respuesta
        print("\nTIEMPOS DE RESPUESTA:")
        for i in I:
            for t in T:
                asignaciones = [(j, params['Tijt'][i,j,t]) 
                               for j in J if Z[i,j,t].X > 0.5]
                if asignaciones:
                    print(f"\nZona {i}, Hora {t}:")
                    for j, tiempo in asignaciones:
                        print(f"- Desde estación {j}: {tiempo:.1f} minutos")

    else:
        print("\nNo se encontró solución óptima")
        if m.status == GRB.INFEASIBLE:
            print("El modelo es infactible")
        elif m.status == GRB.UNBOUNDED:
            print("El modelo es no acotado")
        else:
            print(f"Estado del modelo: {m.status}")