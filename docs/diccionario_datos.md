# Diccionario de Datos — Northwind BI

> **Alcance:** capa Gold y modelo semántico de Power BI  
> **Última revisión:** 2026-10-15  
> **Fuente de verdad:** archivos Parquet de `data/gold/`

## 1. Convenciones

- **PK:** clave primaria, única y no nula.
- **FK:** clave foránea relacionada con una dimensión.
- Los importes monetarios están expresados en dólares.
- Las fechas no contienen componente horario relevante para el análisis.
- `Sin Región` es el valor estandarizado para regiones no informadas.
- El grano de `Fact_Ventas` es una línea de producto dentro de un pedido.

## 2. Inventario de tablas Gold

| Tabla | Tipo | Filas | Grano |
| :--- | :--- | ---: | :--- |
| `Fact_Ventas` | Hechos | 2,155 | Una línea de producto por pedido |
| `Dim_Calendario` | Dimensión | 1,096 | Una fecha calendario |
| `Dim_Cliente` | Dimensión | 91 | Un cliente |
| `Dim_Producto` | Dimensión | 77 | Un producto |
| `Dim_Empleado` | Dimensión | 9 | Un empleado |
| `Dim_Transportista` | Dimensión | 3 | Un transportista |

## 3. Tabla de hechos

### `Fact_Ventas`

Integra la cabecera y el detalle de los pedidos. Su clave lógica compuesta es
`orderID` + `productID`.

| Campo | Tipo | Rol | Nulos | Descripción |
| :--- | :--- | :--- | ---: | :--- |
| `orderID` | Entero | Clave degenerada | 0 | Identificador del pedido; se repite por cada producto vendido. |
| `productID` | Entero | FK | 0 | Producto vendido; relaciona con `Dim_Producto`. |
| `unitPrice` | Decimal | Métrica | 0 | Precio unitario pactado en la línea del pedido. |
| `quantity` | Entero | Métrica | 0 | Cantidad de unidades vendidas. |
| `discount` | Decimal | Métrica | 0 | Tasa de descuento expresada entre 0 y 1. |
| `importeBruto` | Decimal | Métrica | 0 | `quantity × unitPrice`. |
| `importeDescuento` | Decimal | Métrica | 0 | `importeBruto × discount`. |
| `importeNeto` | Decimal | Métrica | 0 | `importeBruto - importeDescuento`. |
| `customerID` | Texto | FK | 0 | Cliente que realizó el pedido; relaciona con `Dim_Cliente`. |
| `employeeID` | Entero | FK | 0 | Empleado responsable; relaciona con `Dim_Empleado`. |
| `shipperID` | Entero | FK | 0 | Transportista del pedido; relaciona con `Dim_Transportista`. |
| `orderDate` | Fecha | FK | 0 | Fecha del pedido; relaciona con `Dim_Calendario`. |
| `requiredDate` | Fecha | Atributo | 0 | Fecha límite solicitada para el envío. |
| `shippedDate` | Fecha | Atributo | 73 | Fecha real de despacho; es nula cuando el pedido está pendiente. |
| `estadoEnvio` | Texto | Atributo | 0 | Clasificación: `A Tiempo`, `Demorado` o `Pendiente`. |
| `shipCountry` | Texto | Atributo | 0 | País de destino del pedido. |
| `shipCity` | Texto | Atributo | 0 | Ciudad de destino del pedido. |
| `shipRegion` | Texto | Atributo | 0 | Región de destino o `Sin Región`. |
| `freight` | Decimal | Métrica de cabecera | 0 | Costo de flete del pedido, repetido en sus líneas; debe agregarse una sola vez por `orderID`. |

## 4. Dimensiones

### `Dim_Calendario`

Calendario diario continuo desde 1996-01-01 hasta 1998-12-31.

| Campo | Tipo | Rol | Descripción |
| :--- | :--- | :--- | :--- |
| `date` | Fecha | PK | Fecha calendario única. |
| `year` | Entero | Jerarquía | Año calendario. |
| `quarter` | Entero | Jerarquía | Número de trimestre, de 1 a 4. |
| `quarterName` | Texto | Etiqueta | Trimestre en formato `T1` a `T4`. |
| `month` | Entero | Orden | Número de mes, de 1 a 12. |
| `monthName` | Texto | Etiqueta | Nombre del mes en español. |
| `monthYear` | Texto | Eje temporal | Periodo en formato `YYYY-MM`. |
| `day` | Entero | Jerarquía | Día del mes. |
| `dayOfWeek` | Entero | Orden | Día de la semana; lunes es 0 y domingo es 6. |
| `dayName` | Texto | Etiqueta | Nombre del día en español. |
| `isWeekend` | Booleano | Bandera | Indica sábado o domingo. |

### `Dim_Cliente`

| Campo | Tipo | Rol | Descripción |
| :--- | :--- | :--- | :--- |
| `customerID` | Texto | PK | Código único del cliente. |
| `companyName` | Texto | Atributo | Razón social del cliente. |
| `contactName` | Texto | Atributo | Nombre del contacto principal. |
| `contactTitle` | Texto | Atributo | Cargo del contacto. |
| `address` | Texto | Atributo | Dirección comercial. |
| `city` | Texto | Geografía | Ciudad del cliente. |
| `region` | Texto | Geografía | Región del cliente o `Sin Región`. |
| `postalCode` | Texto | Geografía | Código postal conservado como texto. |
| `country` | Texto | Geografía | País del cliente. |
| `phone` | Texto | Atributo | Número telefónico. |

### `Dim_Producto`

Dimensión desnormalizada con información de categoría y proveedor.

| Campo | Tipo | Rol | Descripción |
| :--- | :--- | :--- | :--- |
| `productID` | Entero | PK | Identificador único del producto. |
| `productName` | Texto | Atributo | Nombre comercial del producto. |
| `categoryName` | Texto | Agrupación | Categoría del producto. |
| `categoryDescription` | Texto | Atributo | Descripción de la categoría. |
| `supplierName` | Texto | Atributo | Nombre del proveedor. |
| `supplierCountry` | Texto | Geografía | País del proveedor. |
| `unitPriceLista` | Decimal | Métrica descriptiva | Precio de catálogo actual. |
| `unitsInStock` | Entero | Inventario | Unidades disponibles. |
| `unitsOnOrder` | Entero | Inventario | Unidades solicitadas al proveedor. |
| `reorderLevel` | Entero | Inventario | Nivel que activa la reposición. |
| `discontinuedStatus` | Texto | Estado | `Activo` o `Descontinuado`. |

### `Dim_Empleado`

| Campo | Tipo | Rol | Nulos | Descripción |
| :--- | :--- | :--- | ---: | :--- |
| `employeeID` | Entero | PK | 0 | Identificador único del empleado. |
| `fullName` | Texto | Atributo | 0 | Nombre y apellido concatenados. |
| `lastName` | Texto | Atributo | 0 | Apellido. |
| `firstName` | Texto | Atributo | 0 | Nombre. |
| `title` | Texto | Atributo | 0 | Puesto laboral. |
| `titleOfCourtesy` | Texto | Atributo | 0 | Tratamiento de cortesía. |
| `birthDate` | Fecha | Atributo | 0 | Fecha de nacimiento. |
| `hireDate` | Fecha | Atributo | 0 | Fecha de contratación. |
| `city` | Texto | Geografía | 0 | Ciudad del empleado. |
| `region` | Texto | Geografía | 0 | Región del empleado. |
| `country` | Texto | Geografía | 0 | País del empleado. |
| `reportsTo` | Entero | Jerarquía | 1 | Identificador del superior; nulo para la raíz organizacional. |

### `Dim_Transportista`

| Campo | Tipo | Rol | Descripción |
| :--- | :--- | :--- | :--- |
| `shipperID` | Entero | PK | Identificador único del transportista. |
| `companyName` | Texto | Atributo | Nombre de la empresa transportista. |
| `phone` | Texto | Atributo | Número telefónico. |

## 5. Relaciones del modelo semántico

| Dimensión | PK | FK en `Fact_Ventas` | Cardinalidad | Filtro |
| :--- | :--- | :--- | :--- | :--- |
| `Dim_Calendario` | `date` | `orderDate` | 1:N | Simple |
| `Dim_Cliente` | `customerID` | `customerID` | 1:N | Simple |
| `Dim_Producto` | `productID` | `productID` | 1:N | Simple |
| `Dim_Empleado` | `employeeID` | `employeeID` | 1:N | Simple |
| `Dim_Transportista` | `shipperID` | `shipperID` | 1:N | Simple |

## 6. Medidas DAX

Las medidas se almacenan en la tabla técnica `_Medidas`.

### Ventas

| Medida | Definición funcional |
| :--- | :--- |
| `Ventas Brutas` | Suma de `importeBruto`. |
| `Descuentos Otorgados` | Suma de `importeDescuento`. |
| `Ventas Netas` | Suma de `importeNeto`. |
| `Porcentaje Descuento` | Descuentos divididos entre ventas brutas. |

### Actividad comercial

| Medida | Definición funcional |
| :--- | :--- |
| `Total Pedidos` | Conteo distinto de `orderID`. |
| `Unidades Vendidas` | Suma de `quantity`. |
| `Clientes con Compras` | Conteo distinto de clientes presentes en ventas. |
| `Productos Vendidos` | Conteo distinto de productos presentes en ventas. |
| `Ticket Promedio` | Ventas netas divididas entre pedidos. |
| `Precio Promedio de Venta` | Ventas netas divididas entre unidades vendidas. |

### Logística

| Medida | Definición funcional |
| :--- | :--- |
| `Pedidos a Tiempo` | Pedidos distintos con estado `A Tiempo`. |
| `Pedidos Demorados` | Pedidos distintos con estado `Demorado`. |
| `Pedidos Pendientes` | Pedidos distintos con estado `Pendiente`. |
| `Pedidos Enviados` | Pedidos distintos no pendientes. |
| `On-Time Delivery %` | Pedidos a tiempo divididos entre pedidos enviados. |
| `Promedio Días Despacho` | Promedio de días entre pedido y despacho para pedidos enviados. |
| `Flete Total` | Suma del flete una sola vez por pedido. |
| `Flete Promedio por Pedido` | Flete total dividido entre pedidos. |
| `Pedidos Demorados %` | Pedidos demorados divididos entre enviados. |
| `Pedidos Pendientes %` | Pedidos pendientes divididos entre pedidos totales. |

### Inteligencia temporal

| Medida | Definición funcional |
| :--- | :--- |
| `Ventas Netas PY` | Ventas netas del mismo periodo del año anterior. |
| `Variación Ventas YoY` | Diferencia absoluta contra el año anterior; queda vacía sin comparativo. |
| `Crecimiento Ventas YoY %` | Variación interanual porcentual. |
| `Ventas Netas YTD` | Ventas acumuladas desde el inicio del año. |
| `Ventas Netas QTD` | Ventas acumuladas desde el inicio del trimestre. |
| `Ventas Netas MTD` | Ventas acumuladas desde el inicio del mes. |
| `Ventas Mes Anterior` | Ventas netas del mes inmediatamente anterior. |
| `Variación Ventas MoM` | Diferencia absoluta contra el mes anterior. |
| `Crecimiento Ventas MoM %` | Variación mensual porcentual. |

### Análisis de clientes

| Medida | Definición funcional |
| :--- | :--- |
| `Ranking Cliente` | Posición del cliente por ventas netas dentro de la selección. |
| `Ventas Acumuladas Clientes` | Suma progresiva según el ranking de clientes. |
| `Ventas Acumuladas Clientes %` | Participación acumulada sobre las ventas seleccionadas. |
| `Referencia 80 %` | Línea constante del 80% para el análisis Pareto. |

## 7. Reglas críticas de uso

1. No sumar directamente `freight` por línea: el valor se repite para todos los productos del pedido. Utilizar `Flete Total`.
2. Contar pedidos con `DISTINCTCOUNT(orderID)`, nunca mediante conteo de filas.
3. Utilizar `importeNeto` para ingresos realizados después de descuentos.
4. Usar `Dim_Calendario` en ejes y filtros temporales para mantener correctas las medidas de inteligencia de tiempo.
5. Diferenciar el país del cliente (`Dim_Cliente[country]`) del país de destino (`Fact_Ventas[shipCountry]`).
6. Excluir los pedidos pendientes del denominador de `On-Time Delivery %`.
