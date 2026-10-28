
import sqlite3
from pathlib import Path

# Ubicación de la base de datos de NEXTREP
RAIZ = Path(__file__).resolve().parent.parent
BASE_DATOS = RAIZ / "database" / "nextrep_gastos.db"


def consultar_total(cursor, tabla, columna="valor"):
    """Consulta un total y devuelve cero si la tabla o columna no existe."""

    tablas_permitidas = ("ventas", "gastos", "costos", "cobros")

    if tabla not in tablas_permitidas:
        return 0

    cursor.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table' AND name = ?
        """,
        (tabla,)
    )

    if cursor.fetchone() is None:
        return 0

    cursor.execute(f"PRAGMA table_info({tabla})")
    columnas = [fila[1] for fila in cursor.fetchall()]

    if columna not in columnas:
        return 0

    # En cobros solo se suman los que estén pagados, si existe la columna.
    if tabla == "cobros" and "estado" in columnas:
        cursor.execute(
            f"""
            SELECT COALESCE(SUM({columna}), 0)
            FROM {tabla}
            WHERE estado = ?
            """,
            ("Pagado",)
        )
    else:
        cursor.execute(
            f"SELECT COALESCE(SUM({columna}), 0) FROM {tabla}"
        )

    return cursor.fetchone()[0] or 0


def analizar_negocio():
    # Verificar que exista la base de datos
    if not BASE_DATOS.exists():
        print("No se encuentra la base de datos de NEXTREP.")
        print("Verifica la ubicación del archivo nextrep_gastos.db.")
        return

    conexion = sqlite3.connect(BASE_DATOS)

    try:
        cursor = conexion.cursor()

        # Consultar los valores registrados
        ventas = consultar_total(cursor, "ventas", "total")
        cobros = consultar_total(cursor, "cobros", "valor")
        gastos = consultar_total(cursor, "gastos", "valor")
        costos = consultar_total(cursor, "costos", "valor")

        # Calcular resultados financieros estimados
        egresos = gastos + costos
        balance = ventas - egresos

        if ventas > 0:
            rentabilidad = (balance / ventas) * 100
            porcentaje_egresos = (egresos / ventas) * 100
        else:
            rentabilidad = 0
            porcentaje_egresos = 0

    except sqlite3.Error as error:
        print("No fue posible consultar la base de datos.")
        print(f"Detalle: {error}")
        return

    finally:
        conexion.close()

    # Mostrar resultados
    print("\n===========================================")
    print("       ANALISIS INTELIGENTE DE NEXTREP")
    print("===========================================")
    print(f"Ventas registradas:       ${ventas:,.0f}")
    print(f"Cobros pagados:           ${cobros:,.0f}")
    print(f"Gastos registrados:       ${gastos:,.0f}")
    print(f"Costos registrados:       ${costos:,.0f}")
    print(f"Total de egresos:         ${egresos:,.0f}")
    print(f"Balance estimado:         ${balance:,.0f}")
    print(f"Rentabilidad estimada:    {rentabilidad:.2f}%")
    print(f"Egresos sobre ventas:     {porcentaje_egresos:.2f}%")

    # Generar recomendaciones
    print("\nRecomendacion:")

    if ventas == 0 and egresos == 0:
        print("Registra ventas y gastos para comenzar el analisis.")

    elif ventas == 0:
        print("Alerta: hay egresos, pero no se registran ventas.")
        print("Revisa los movimientos y registra tus ingresos.")

    elif balance < 0:
        print("Alerta: los gastos y costos superan las ventas.")
        print("Revisa los egresos y busca formas de reducirlos.")

    elif porcentaje_egresos >= 70:
        print("Atencion: los egresos representan el 70% o mas de las ventas.")
        print("Analiza los gastos y costos para mejorar el balance.")

    else:
        print("La situacion financiera presenta un balance favorable.")
        print("Continua registrando tus movimientos y revisando los resultados.")

    print("===========================================\n")


if __name__ == "__main__":
    analizar_negocio()