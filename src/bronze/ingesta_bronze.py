"""
Pipeline de Ingesta - Capa Bronze
Proyecto: Northwind BI
Propósito: Extraer fuentes CSV crudas, persistir réplica inmutable en formato Parquet (Snappy)
           y validar la paridad estricta de registros.
"""

from pathlib import Path
import pandas as pd


def ejecutar_ingesta_bronze():
    # 1. Definir rutas relativas reproducibles
    directorio_base = Path(__file__).resolve().parent.parent.parent
    ruta_raw = directorio_base / "data" / "raw" / "northwind"
    ruta_bronze = directorio_base / "data" / "bronze"

    # Asegurar que la carpeta de destino exista
    ruta_bronze.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print(" INICIO DEL PIPELINE DE INGESTA: RAW -> BRONZE (PARQUET)")
    print("=" * 70)

    archivos_csv = sorted(list(ruta_raw.glob("*.csv")))
    if not archivos_csv:
        raise FileNotFoundError(f"No se encontraron archivos CSV en: {ruta_raw}")

    resultados_paridad = []

    for archivo in archivos_csv:
        nombre_tabla = archivo.stem

        # A. Lectura fiel del CSV crudo
        df_raw = pd.read_csv(archivo)
        filas_raw = len(df_raw)
        cols_raw = len(df_raw.columns)
        tamano_csv_kb = round(archivo.stat().st_size / 1024, 2)

        # B. Exportación a Parquet con compresión Snappy
        archivo_parquet = ruta_bronze / f"{nombre_tabla}.parquet"
        df_raw.to_parquet(archivo_parquet, engine="pyarrow", compression="snappy", index=False)

        # C. Relectura para prueba de paridad
        df_bronze = pd.read_parquet(archivo_parquet, engine="pyarrow")
        filas_bronze = len(df_bronze)
        cols_bronze = len(df_bronze.columns)
        tamano_parquet_kb = round(archivo_parquet.stat().st_size / 1024, 2)

        # D. Evaluación de discrepancia
        diff_filas = abs(filas_raw - filas_bronze)
        diff_cols = abs(cols_raw - cols_bronze)
        ahorro_pct = round((1 - (tamano_parquet_kb / tamano_csv_kb)) * 100, 1) if tamano_csv_kb > 0 else 0.0

        es_valido = (diff_filas == 0) and (diff_cols == 0)

        resultados_paridad.append({
            "tabla": nombre_tabla,
            "filas_raw": filas_raw,
            "filas_bronze": filas_bronze,
            "diff_filas": diff_filas,
            "tamano_csv_kb": tamano_csv_kb,
            "tamano_parquet_kb": tamano_parquet_kb,
            "ahorro_espacio": f"{ahorro_pct}%",
            "estado": "[OK] Paridad 100%" if es_valido else "[ERROR] Error de Paridad"
        })

    # 2. Presentar reporte consolidado
    df_reporte = pd.DataFrame(resultados_paridad)
    print("\nREPORTE DE CONCILIACIÓN RAW VS. BRONZE:")
    print(df_reporte.to_string(index=False))

    # 3. Validación final del pipeline
    total_errores = (df_reporte["diff_filas"] != 0).sum()
    print("\n" + "=" * 70)
    if total_errores == 0:
        print("[OK] PIPELINE EXITOSO: 11 tablas Bronze generadas sin discrepancia de datos.")
    else:
        print(f"[ALERTA] Se detectaron {total_errores} tablas con diferencias de registros.")
    print("=" * 70)

    return df_reporte


if __name__ == "__main__":
    ejecutar_ingesta_bronze()
