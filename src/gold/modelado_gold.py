"""
Pipeline de modelado dimensional - Capa Gold.

Lee las tablas Silver, construye cinco dimensiones conformadas y Fact_Ventas,
valida la integridad referencial y exporta el modelo estrella a data/gold/.
"""

from pathlib import Path

import pandas as pd


MESES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
}

DIAS = {
    0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves",
    4: "Viernes", 5: "Sábado", 6: "Domingo",
}


def cargar_silver(ruta_silver):
    nombres = [
        "orders", "order-details", "products", "categories",
        "suppliers", "customers", "employees", "shippers",
    ]
    return {
        nombre: pd.read_parquet(ruta_silver / f"{nombre}.parquet")
        for nombre in nombres
    }


def construir_dim_calendario():
    calendario = pd.DataFrame({
        "date": pd.date_range(start="1996-01-01", end="1998-12-31", freq="D")
    })
    calendario["year"] = calendario["date"].dt.year
    calendario["quarter"] = calendario["date"].dt.quarter
    calendario["quarterName"] = "T" + calendario["quarter"].astype(str)
    calendario["month"] = calendario["date"].dt.month
    calendario["monthName"] = calendario["month"].map(MESES)
    calendario["monthYear"] = calendario["date"].dt.strftime("%Y-%m")
    calendario["day"] = calendario["date"].dt.day
    calendario["dayOfWeek"] = calendario["date"].dt.dayofweek
    calendario["dayName"] = calendario["dayOfWeek"].map(DIAS)
    calendario["isWeekend"] = calendario["dayOfWeek"].isin([5, 6])
    return calendario


def construir_modelo(tablas):
    dim_cliente = tablas["customers"][[
        "customerID", "companyName", "contactName", "contactTitle",
        "address", "city", "region", "postalCode", "country", "phone",
    ]].copy()

    dim_producto = tablas["products"].merge(
        tablas["categories"][["categoryID", "categoryName", "description"]]
        .rename(columns={"description": "categoryDescription"}),
        on="categoryID",
        how="left",
        validate="many_to_one",
    ).merge(
        tablas["suppliers"][["supplierID", "companyName", "country"]]
        .rename(columns={
            "companyName": "supplierName",
            "country": "supplierCountry",
        }),
        on="supplierID",
        how="left",
        validate="many_to_one",
    ).rename(columns={"unitPrice": "unitPriceLista"})
    dim_producto = dim_producto[[
        "productID", "productName", "categoryName", "categoryDescription",
        "supplierName", "supplierCountry", "unitPriceLista", "unitsInStock",
        "unitsOnOrder", "reorderLevel", "discontinuedStatus",
    ]].copy()

    dim_empleado = tablas["employees"][[
        "employeeID", "fullName", "lastName", "firstName", "title",
        "titleOfCourtesy", "birthDate", "hireDate", "city", "region",
        "country", "reportsTo",
    ]].copy()

    dim_transportista = tablas["shippers"][[
        "shipperID", "companyName", "phone",
    ]].copy()

    orders = tablas["orders"].rename(columns={"shipVia": "shipperID"})
    fact_ventas = tablas["order-details"].merge(
        orders[[
            "orderID", "customerID", "employeeID", "shipperID", "orderDate",
            "requiredDate", "shippedDate", "estadoEnvio", "shipCountry",
            "shipCity", "shipRegion", "freight",
        ]],
        on="orderID",
        how="left",
        validate="many_to_one",
    )
    fact_ventas["importeBruto"] = (
        fact_ventas["quantity"] * fact_ventas["unitPrice"]
    ).round(2)
    fact_ventas["importeDescuento"] = (
        fact_ventas["importeBruto"] * fact_ventas["discount"]
    ).round(2)
    fact_ventas["importeNeto"] = (
        fact_ventas["importeBruto"] - fact_ventas["importeDescuento"]
    ).round(2)

    return {
        "Dim_Calendario": construir_dim_calendario(),
        "Dim_Cliente": dim_cliente,
        "Dim_Producto": dim_producto,
        "Dim_Empleado": dim_empleado,
        "Dim_Transportista": dim_transportista,
        "Fact_Ventas": fact_ventas,
    }


def validar_modelo(tablas_gold):
    fact = tablas_gold["Fact_Ventas"]
    relaciones = {
        "productID": tablas_gold["Dim_Producto"]["productID"],
        "customerID": tablas_gold["Dim_Cliente"]["customerID"],
        "employeeID": tablas_gold["Dim_Empleado"]["employeeID"],
        "shipperID": tablas_gold["Dim_Transportista"]["shipperID"],
    }

    for clave, claves_dimension in relaciones.items():
        if fact[clave].isna().any() or (~fact[clave].isin(claves_dimension)).any():
            raise ValueError(f"Integridad referencial inválida para {clave}.")

    fechas = pd.to_datetime(fact["orderDate"]).dt.normalize()
    calendario = pd.to_datetime(tablas_gold["Dim_Calendario"]["date"]).dt.normalize()
    if fechas.isna().any() or (~fechas.isin(calendario)).any():
        raise ValueError("Integridad referencial inválida para orderDate.")

    esperados = {
        "filas": 2155,
        "pedidos": 830,
        "bruto": 1354458.59,
        "descuento": 88665.57,
        "neto": 1265793.02,
    }
    obtenidos = {
        "filas": len(fact),
        "pedidos": fact["orderID"].nunique(),
        "bruto": round(fact["importeBruto"].sum(), 2),
        "descuento": round(fact["importeDescuento"].sum(), 2),
        "neto": round(fact["importeNeto"].sum(), 2),
    }
    if obtenidos != esperados:
        raise ValueError(f"Conciliación financiera inválida: {obtenidos}")


def exportar_modelo(tablas_gold, ruta_gold):
    ruta_gold.mkdir(parents=True, exist_ok=True)
    for nombre, tabla in tablas_gold.items():
        ruta_archivo = ruta_gold / f"{nombre}.parquet"
        tabla.to_parquet(
            ruta_archivo, engine="pyarrow", compression="snappy", index=False
        )
        if len(pd.read_parquet(ruta_archivo)) != len(tabla):
            raise ValueError(f"La exportación de {nombre} alteró el número de filas.")


def ejecutar_modelado_gold():
    directorio_base = Path(__file__).resolve().parent.parent.parent
    ruta_silver = directorio_base / "data" / "silver"
    ruta_gold = directorio_base / "data" / "gold"

    tablas_gold = construir_modelo(cargar_silver(ruta_silver))
    validar_modelo(tablas_gold)
    exportar_modelo(tablas_gold, ruta_gold)

    print("=== CAPA GOLD GENERADA Y VALIDADA ===")
    for nombre, tabla in tablas_gold.items():
        print(f"[OK] {nombre:<20} {len(tabla):>5} filas")
    fact = tablas_gold["Fact_Ventas"]
    print(f"Venta neta total: ${fact['importeNeto'].sum():,.2f}")
    print(f"Directorio: {ruta_gold}")

    return tablas_gold


if __name__ == "__main__":
    ejecutar_modelado_gold()
