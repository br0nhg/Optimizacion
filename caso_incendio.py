def resolver_caso_incendio(coords_incendio, hora_actual):
    """
    Resuelve un caso específico de incendio
    
    Args:
        coords_incendio: Tupla (latitud, longitud)
        hora_actual: Hora del día (0-23)
    """
    print("\n=== ANÁLISIS DE CASO DE INCENDIO ===")
    print(f"Coordenadas: {coords_incendio}")
    print(f"Hora: {hora_actual}:00")
    
    try:
        # 1. Identificar comuna más cercana
        distancias_comunas = {}
        comuna_index = None  # Para guardar el índice de la comuna afectada
        for i, (comuna, datos) in enumerate(COMUNAS.items(), 1):
            dist = geodesic(coords_incendio, datos['coords']).kilometers
            distancias_comunas[comuna] = dist
            if comuna == min(distancias_comunas.items(), key=lambda x: x[1])[0]:
                comuna_index = i
        
        comuna_cercana = min(distancias_comunas.items(), key=lambda x: x[1])[0]
        print(f"\nComuna más cercana: {comuna_cercana}")
        print(f"Distancia al centro de la comuna: {distancias_comunas[comuna_cercana]:.2f} km")

        # 2. Modificar parámetros para considerar solo la comuna afectada
        params = generar_parametros()
        
        # Modificar Dit para que solo la comuna afectada tenga demanda
        for i in I:
            for t in T:
                if i != comuna_index:  # Si no es la comuna afectada
                    params['Dit'][i,t] = 0  # No hay demanda
                elif t != hora_actual:  # Si no es la hora actual
                    params['Dit'][i,t] = 0  # No hay demanda en otros tiempos

        # 3. Crear y resolver modelo
        m, X, Y, Z, EE, FF, V, U = crear_modelo_optimizacion(params, I, J, T)
        m.optimize()

        if m.status == GRB.OPTIMAL:
            print("\n=== PLAN DE RESPUESTA RECOMENDADO ===")
            print(f"Valor objetivo (tiempo total ponderado): {m.objVal:.2f} minutos")
            
            # Mostrar asignaciones para la comuna afectada
            asignaciones = []
            for j in J:
                if X[comuna_index,j,hora_actual].X > 0:
                    est = list(ESTACIONES_BOMBEROS.keys())[j-1]
                    est_data = ESTACIONES_BOMBEROS[est]
                    asignaciones.append({
                        'estacion': est_data['nombre'],
                        'bomberos': int(X[comuna_index,j,hora_actual].X),
                        'carros': int(Y[comuna_index,j,hora_actual].X),
                        'tiempo': params['Tijt'][comuna_index,j,hora_actual]
                    })

            # Ordenar asignaciones por tiempo de respuesta
            asignaciones.sort(key=lambda x: x['tiempo'])
            
            # Mostrar resumen
            print(f"\nRecursos totales asignados:")
            print(f"- Bomberos: {sum(a['bomberos'] for a in asignaciones)}")
            print(f"- Carros: {sum(a['carros'] for a in asignaciones)}")
            
            print("\nDistribución de recursos:")
            for i, asig in enumerate(asignaciones, 1):
                print(f"\n{i}. Desde {asig['estacion']}:")
                print(f"   - Bomberos a enviar: {asig['bomberos']}")
                print(f"   - Carros a enviar: {asig['carros']}")
                print(f"   - Tiempo estimado: {asig['tiempo']:.1f} minutos")

            # Generar reporte detallado
            generar_reporte_caso(
                comuna_cercana,
                hora_actual,
                coords_incendio,
                asignaciones,
                m.objVal
            )

            return True
        else:
            print("\nNo se pudo encontrar una solución óptima")
            return False

    except Exception as e:
        print(f"Error en el análisis del caso: {e}")
        return False

def generar_reporte_caso(comuna, hora, coords, asignaciones, valor_objetivo):
    """Genera un reporte detallado del caso"""
    import os
    from datetime import datetime
    
    # Crear directorio si no existe
    if not os.path.exists('reportes'):
        os.makedirs('reportes')
    
    # Generar nombre de archivo con timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"reportes/caso_incendio_{timestamp}.txt"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("=== REPORTE DE CASO DE INCENDIO ===\n\n")
        f.write(f"Fecha y hora del reporte: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Comuna afectada: {comuna}\n")
        f.write(f"Hora del incendio: {hora}:00\n")
        f.write(f"Coordenadas: {coords}\n")
        f.write(f"Valor objetivo (tiempo total): {valor_objetivo:.2f} minutos\n\n")
        
        f.write("ASIGNACIÓN DE RECURSOS\n")
        f.write("=====================\n\n")
        
        total_bomberos = sum(a['bomberos'] for a in asignaciones)
        total_carros = sum(a['carros'] for a in asignaciones)
        tiempo_promedio = sum(a['tiempo'] for a in asignaciones) / len(asignaciones)
        
        f.write(f"Recursos totales:\n")
        f.write(f"- Bomberos asignados: {total_bomberos}\n")
        f.write(f"- Carros asignados: {total_carros}\n")
        f.write(f"- Tiempo promedio de respuesta: {tiempo_promedio:.1f} minutos\n\n")
        
        f.write("Distribución por estación:\n")
        for i, asig in enumerate(asignaciones, 1):
            f.write(f"\n{i}. {asig['estacion']}\n")
            f.write(f"   Bomberos: {asig['bomberos']}\n")
            f.write(f"   Carros: {asig['carros']}\n")
            f.write(f"   Tiempo estimado: {asig['tiempo']:.1f} minutos\n")
    
    print(f"\nReporte generado: {filename}")