from gurobipy import GRB, Model, quicksum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def crear_modelo_optimizacion(params, I, J, T):
    try:
        m = Model("planificacion_bomberos")
        
        # Variables de decisión (igual que antes)
        X = m.addVars(I, J, T, vtype=GRB.INTEGER, name="bomberos")
        Y = m.addVars(I, J, T, vtype=GRB.INTEGER, name="carros")
        Z = m.addVars(I, J, T, vtype=GRB.BINARY, name="salida_carros")
        EE = m.addVars(J, T, vtype=GRB.INTEGER, name="bomberos_disponibles")
        FF = m.addVars(J, T, vtype=GRB.INTEGER, name="carros_disponibles")
        V = m.addVars(J, T, vtype=GRB.INTEGER, name="bomberos_devueltos")
        U = m.addVars(J, T, vtype=GRB.INTEGER, name="carros_devueltos")

        m.update()

        # Restricciones modificadas para ser más flexibles
        
        # 1. Satisfacción de la demanda
        m.addConstrs(
            (quicksum(X[i,j,t] for j in J) >= params['Dit'][i,t] 
             for i in I for t in T),
            name="R1_demanda"
        )

        # 2. Capacidad de bomberos
        m.addConstrs(
            (quicksum(X[i,j,t] for i in I) <= params['Ej'][j]
             for j in J for t in T),
            name="R2_cap_bomberos"
        )

        # 3. Capacidad de carros (relajada)
        m.addConstrs(
            (quicksum(Y[i,j,t] for i in I) <= params['Fj'][j]
             for j in J for t in T),
            name="R3_cap_carros"
        )

        # 4. Balance inicial bomberos (modificado)
        m.addConstrs(
            (EE[j,0] == params['Ej'][j] - quicksum(X[i,j,0] for i in I)
             for j in J),
            name="R4_balance_inicial_bomberos"
        )

        # 5. Balance bomberos (modificado)
        m.addConstrs(
            (EE[j,t] == EE[j,t-1] - quicksum(X[i,j,t] for i in I) + V[j,t]
             for j in J for t in T if t > 0),
            name="R5_balance_bomberos"
        )

        # 6. Balance inicial carros (modificado)
        m.addConstrs(
            (FF[j,0] == params['Fj'][j] - quicksum(Y[i,j,0] for i in I)
             for j in J),
            name="R6_balance_inicial_carros"
        )

        # 7. Balance carros (modificado)
        m.addConstrs(
            (FF[j,t] == FF[j,t-1] - quicksum(Y[i,j,t] for i in I) + U[j,t]
             for j in J for t in T if t > 0),
            name="R7_balance_carros"
        )

        # 8. Relación bomberos-carros (relajada)
        m.addConstrs(
            (X[i,j,t] <= params['Cmax'] * Y[i,j,t]
             for i in I for j in J for t in T),
            name="R8_relacion_bomberos_carros"
        )

        # 9. Retorno bomberos (modificado)
        for j in J:
            for t in T:
                if t > 0:  # Solo para t > 0
                    m.addConstr(
                        (V[j,t] == quicksum(X[i,j,max(0, t-params['tau'][i,t])] 
                                          for i in I)),
                        name=f"R9_retorno_bomberos_{j}_{t}"
                    )

        # 10. Retorno carros (modificado)
        for j in J:
            for t in T:
                if t > 0:  # Solo para t > 0
                    m.addConstr(
                        (U[j,t] == quicksum(Y[i,j,max(0, t-params['tau'][i,t])] 
                                          for i in I)),
                        name=f"R10_retorno_carros_{j}_{t}"
                    )

        # 11-12. Control de variable Z (relajada)
        m.addConstrs(
            (Z[i,j,t] <= Y[i,j,t] for i in I for j in J for t in T),
            name="R11_control_Z"
        )

        # Función objetivo
        objetivo = quicksum(
            (params['Tijt'][i,j,t] * Z[i,j,t] + params['Rjt'][j,t] * X[i,j,t])
            for i in I for j in J for t in T
        )
        
        m.setObjective(objetivo, GRB.MINIMIZE)

        # Configuración para debug
        m.setParam('InfUnbdInfo', 1)  # Para obtener información sobre infactibilidad
        
        return m, X, Y, Z, EE, FF, V, U

    except Exception as e:
        logger.error(f"Error en la creación del modelo: {e}")
        raise