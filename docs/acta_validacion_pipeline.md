# Acta de Validación Integral del Pipeline Northwind BI

## Información general

- **Fecha de validación:** 2026-10-11 10:55:52
- **Capas auditadas:** Raw, Bronze, Silver y Gold
- **Resultado general:** APROBADO
- **Notebook de evidencia:** `notebooks/05_validacion_final.ipynb`

## Conciliación de registros

| Indicador | Raw | Bronze | Silver | Gold |
| :--- | ---: | ---: | ---: | ---: |
| Pedidos únicos | 830 | 830 | 830 | 830 |
| Líneas de pedido | 2155 | 2155 | 2155 | 2155 |

No se detectaron registros perdidos ni duplicados durante el procesamiento.

## Conciliación financiera

| Métrica | Raw | Bronze | Silver | Gold | Diferencia Raw-Gold |
| :--- | ---: | ---: | ---: | ---: | ---: |
| Venta bruta | $1,354,458.59 | $1,354,458.59 | $1,354,458.59 | $1,354,458.59 | $0.00 |
| Descuentos | $88,665.57 | $88,665.57 | $88,665.57 | $88,665.57 | $0.00 |
| Venta neta | $1,265,793.02 | $1,265,793.02 | $1,265,793.02 | $1,265,793.02 | $0.00 |

## Controles ejecutados

| control                            | estado   |
|:-----------------------------------|:---------|
| Disponibilidad de las cuatro capas | [OK]     |
| Conciliación de pedidos y líneas   | [OK]     |
| Conciliación financiera            | [OK]     |
| Unicidad de dimensiones Gold       | [OK]     |
| Cobertura temporal                 | [OK]     |
| Integridad referencial             | [OK]     |

## Validación dimensional

- `Dim_Calendario`: 1096 claves únicas.
- `Dim_Cliente`: 91 claves únicas.
- `Dim_Producto`: 77 claves únicas.
- `Dim_Empleado`: 9 claves únicas.
- `Dim_Transportista`: 3 claves únicas.
- Claves primarias duplicadas: 0.
- Claves primarias nulas: 0.
- Claves foráneas huérfanas en `Fact_Ventas`: 0.

## Cobertura temporal

- Rango de `Dim_Calendario`: 1996-01-01 a 1998-12-31.
- Rango de ventas: 1996-07-04 a 1998-05-06.
- Días en calendario: 1096.
- Saltos en la secuencia diaria: 0.
- Ventas fuera del calendario: 0.

## Conclusión

El pipeline superó satisfactoriamente todos los controles de calidad y
conciliación. La capa Gold representa fielmente los datos de origen, con una
diferencia financiera de $0.00 entre Raw y Gold.

**Estado final: APROBADO PARA INTEGRACIÓN CON POWER BI.**
