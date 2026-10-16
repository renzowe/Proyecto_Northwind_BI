"""
Pipeline de Transformación - Capa Silver
Proyecto: Northwind BI
Propósito: Leer tablas de la Capa Bronze (Parquet), aplicar estandarización de textos,
           casteo estricto de tipos de datos, tratamiento justificado de valores nulos
           y métricas financieras precalculadas, exportando a data/silver/*.parquet.
"""

from pathlib import Path
import pandas as pd


def limpiar_textos(df):
    df_limpio = df.copy()
    for col in df_limpio.select_dtypes(include=["object", "string"]).columns:
        df_limpio[col] = df_limpio[col].astype(str).str.strip()
    return df_limpio


def ejecutar_transformacion_silver():
    directorio_base = Path(__file__).resolve().parent.parent.parent
    ruta_bronze = directorio_base / "data" / "bronze"
    ruta_silver = directorio_base / "data" / "silver"

    ruta_silver.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print(" INICIO DEL PIPELINE DE TRANSFORMACIÓN: BRONZE -> SILVER (PARQUET)")
    print("=" * 70)

    # 1. Cargar tablas desde Bronze
    tablas_bronze = {}
    for archivo in ruta_bronze.glob("*.parquet"):
        tablas_bronze[archivo.stem] = pd.read_parquet(archivo, engine="pyarrow")

    tablas_silver = {}

    # 2. Bloque 1: Dimensiones Maestras y Geografía
    tablas_silver["categories"] = limpiar_textos(tablas_bronze["categories"])
    tablas_silver["regions"] = limpiar_textos(tablas_bronze["regions"])
    tablas_silver["territories"] = limpiar_textos(tablas_bronze["territories"])
    tablas_silver["shippers"] = limpiar_textos(tablas_bronze["shippers"])
    tablas_silver["employee-territories"] = limpiar_textos(tablas_bronze["employee-territories"])

    df_sup = limpiar_textos(tablas_bronze["suppliers"])
    df_sup["region"] = df_sup["region"].replace({"nan": "Sin Región", "": "Sin Región"}).fillna("Sin Región")
    df_sup["fax"] = df_sup["fax"].replace({"nan": "Sin Fax", "": "Sin Fax"}).fillna("Sin Fax")
    df_sup["homePage"] = df_sup["homePage"].replace({"nan": "Sin Web", "": "Sin Web"}).fillna("Sin Web")
    tablas_silver["suppliers"] = df_sup

    # 3. Bloque 2: Entidades Principales
    # Customers
    df_cust = limpiar_textos(tablas_bronze["customers"])
    df_cust["region"] = df_cust["region"].replace({"nan": "Sin Región", "": "Sin Región"}).fillna("Sin Región")
    df_cust["postalCode"] = df_cust["postalCode"].replace({"nan": "Sin Código", "": "Sin Código"}).fillna("Sin Código")
    df_cust["fax"] = df_cust["fax"].replace({"nan": "Sin Fax", "": "Sin Fax"}).fillna("Sin Fax")
    tablas_silver["customers"] = df_cust

    # Employees
    df_emp = limpiar_textos(tablas_bronze["employees"])
    df_emp["birthDate"] = pd.to_datetime(df_emp["birthDate"])
    df_emp["hireDate"] = pd.to_datetime(df_emp["hireDate"])
    df_emp["region"] = df_emp["region"].replace({"nan": "Sin Región", "": "Sin Región"}).fillna("Sin Región")
    df_emp["reportsTo"] = pd.to_numeric(df_emp["reportsTo"], errors="coerce").astype("Int64")
    df_emp["fullName"] = df_emp["firstName"] + " " + df_emp["lastName"]
    tablas_silver["employees"] = df_emp

    # Products
    df_prod = limpiar_textos(tablas_bronze["products"])
    df_prod["unitPrice"] = df_prod["unitPrice"].astype(float).round(2)
    df_prod["unitsInStock"] = df_prod["unitsInStock"].astype(int)
    df_prod["unitsOnOrder"] = df_prod["unitsOnOrder"].astype(int)
    df_prod["reorderLevel"] = df_prod["reorderLevel"].astype(int)
    df_prod["discontinuedStatus"] = df_prod["discontinued"].apply(
        lambda x: "Descontinuado" if x == 1 else "Activo"
    )
    tablas_silver["products"] = df_prod

    # 4. Bloque 3: Tablas Transaccionales
    # Orders
    df_ord = limpiar_textos(tablas_bronze["orders"])
    df_ord["orderDate"] = pd.to_datetime(df_ord["orderDate"])
    df_ord["requiredDate"] = pd.to_datetime(df_ord["requiredDate"])
    df_ord["shippedDate"] = pd.to_datetime(df_ord["shippedDate"])
    df_ord["shipRegion"] = df_ord["shipRegion"].replace({"nan": "Sin Región", "": "Sin Región"}).fillna("Sin Región")
    df_ord["shipPostalCode"] = df_ord["shipPostalCode"].replace({"nan": "Sin Código", "": "Sin Código"}).fillna("Sin Código")
    df_ord["freight"] = df_ord["freight"].astype(float).round(2)
    df_ord["diasDespacho"] = (df_ord["shippedDate"] - df_ord["orderDate"]).dt.days

    def clasificar_envio(row):
        if pd.isna(row["shippedDate"]):
            return "Pendiente"
        elif row["shippedDate"] > row["requiredDate"]:
            return "Demorado"
        else:
            return "A Tiempo"

    df_ord["estadoEnvio"] = df_ord.apply(clasificar_envio, axis=1)
    tablas_silver["orders"] = df_ord

    # Order Details
    df_det = tablas_bronze["order-details"].copy()
    df_det["unitPrice"] = df_det["unitPrice"].astype(float).round(2)
    df_det["quantity"] = df_det["quantity"].astype(int)
    df_det["discount"] = df_det["discount"].astype(float).round(4)
    df_det["importeBruto"] = (df_det["unitPrice"] * df_det["quantity"]).round(2)
    df_det["importeDescuento"] = (df_det["unitPrice"] * df_det["quantity"] * df_det["discount"]).round(2)
    df_det["importeNeto"] = (df_det["importeBruto"] - df_det["importeDescuento"]).round(2)
    tablas_silver["order-details"] = df_det

    # 5. Exportar a Parquet
    resumen = []
    for nombre, df in tablas_silver.items():
        ruta_salida = ruta_silver / f"{nombre}.parquet"
        df.to_parquet(ruta_salida, engine="pyarrow", compression="snappy", index=False)
        resumen.append({
            "tabla": nombre,
            "filas": len(df),
            "columnas": len(df.columns),
            "tamano_kb": round(ruta_salida.stat().st_size / 1024, 2)
        })

    df_res = pd.DataFrame(resumen)
    print("\nREPORTE DE GENERACIÓN DE CAPA SILVER:")
    print(df_res.to_string(index=False))
    print("\n" + "=" * 70)
    print("[OK] PIPELINE EXITOSO: 11 tablas Silver generadas en data/silver/")
    print("=" * 70)

    return df_res


if __name__ == "__main__":
    ejecutar_transformacion_silver()
