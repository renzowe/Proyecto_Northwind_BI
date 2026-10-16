# Catálogo de Calidad de Datos y Reglas de Negocio — Northwind BI

> **Documento:** Especificación Técnica de Calidad de Datos  
> **Área:** Ingeniería de Datos y Business Intelligence  
> **Alcance:** Capas Raw, Bronze, Silver y Gold  
> **Estado:** Aprobado y Validado empíricamente en `notebooks/02_calidad_datos.ipynb`

---

## 1. Propósito y Alcance

Este documento establece el **contrato de calidad de datos** para el proyecto Northwind BI. Define formalmente las reglas de validación, las restricciones de integridad referencial, las restricciones de dominio numérico y las políticas de transformación e imputación que se aplicarán de forma obligatoria durante el procesamiento de la **Capa Silver** y la consolidación de la **Capa Gold**.

---

## 2. Resumen Ejecutivo de la Auditoría de Fuentes (Raw)

A partir de la inspección de las 11 tablas del ecosistema Northwind, se concluye:

* **Integridad Referencial:** 100% conforme. Se evaluaron 7 relaciones críticas entre hechos y dimensiones, registrando **0 claves foráneas huérfanas**.
* **Duplicidad:** 100% conforme. Las 11 tablas presentan **0 registros duplicados a nivel de fila completa**.
* **Coherencia Numérica:** 100% conforme. No existen precios negativos, fletes negativos, existencias negativas ni cantidades menores o iguales a cero.
* **Coherencia Temporal:** 100% conforme. No existen pedidos con fecha de despacho anterior a la fecha de orden.
* **Comportamiento Operativo Detectado:** Se identificaron **37 pedidos despachados con retraso** (4.57% del total de despachos), lo que establece la tasa de entrega a tiempo (**On-Time Delivery**) histórica del negocio en **95.43%**.

---

## 3. Catálogo de Claves Primarias y Unicidad

Cada entidad del negocio cuenta con una definición estricta de unicidad:

| Tabla | Tipo de Clave | Columnas Clave | Criterio de Aceptación |
| :--- | :--- | :--- | :--- |
| `categories` | Primaria Simple | `categoryID` | Valor entero único y no nulo. |
| `customers` | Primaria Simple | `customerID` | Código alfanumérico único de 5 caracteres. |
| `employees` | Primaria Simple | `employeeID` | Valor entero único y no nulo. |
| `orders` | Primaria Simple | `orderID` | Entero único y correlativo por pedido. |
| `products` | Primaria Simple | `productID` | Entero único por producto de catálogo. |
| `regions` | Primaria Simple | `regionID` | Entero único por región comercial. |
| `shippers` | Primaria Simple | `shipperID` | Entero único por transportista. |
| `suppliers` | Primaria Simple | `supplierID` | Entero único por proveedor. |
| `territories` | Primaria Simple | `territoryID` | Identificador único por territorio geográfico. |
| `employee-territories` | Primaria Compuesta | `(employeeID, territoryID)` | Par único. Relación N:M entre empleados y zonas. |
| `order-details` | Primaria Compuesta | `(orderID, productID)` | Par único. Granularidad mínima: línea de venta. |

---

## 4. Matriz de Integridad Referencial

Queda prohibida la carga a Silver o Gold de cualquier registro que vulnere las siguientes relaciones verificadas:

| Relación | Origen (FK) | Destino (PK) | Huérfanos Permitidos | Estado Verificado |
| :--- | :--- | :--- | :--- | :--- |
| **Cliente en Orden** | `orders.customerID` | `customers.customerID` | 0 |  Conforme |
| **Vendedor en Orden** | `orders.employeeID` | `employees.employeeID` | 0 |  Conforme |
| **Transportista en Orden** | `orders.shipVia` | `shippers.shipperID` | 0 |  Conforme |
| **Cabecera en Detalle** | `order-details.orderID` | `orders.orderID` | 0 |  Conforme |
| **Producto en Detalle** | `order-details.productID` | `products.productID` | 0 | Conforme |
| **Proveedor en Producto** | `products.supplierID` | `suppliers.supplierID` | 0 |  Conforme |
| **Categoría en Producto** | `products.categoryID` | `categories.categoryID` | 0 |  Conforme |

---

## 5. Reglas de Validación Numéricas y Comerciales

Las transformaciones en la Capa Silver deberán aplicar aserciones para garantizar los siguientes rangos de dominio:

1. **Precios Unitarios de Venta (`order-details.unitPrice`):**
   * Regla: `unitPrice > 0.0`.
   * Rango histórico observado: `$2.00` a `$263.50`.
2. **Cantidades Vendidas (`order-details.quantity`):**
   * Regla: `quantity > 0` y tipo entero.
   * Rango histórico observado: `1` a `130` unidades por línea.
3. **Descuento Comercial (`order-details.discount`):**
   * Regla: `0.0 <= discount <= 1.0`.
   * Política comercial de Northwind: El descuento máximo es del **25% (`0.25`)**. Todo valor superior será considerado anomalía.
4. **Costo de Envío / Flete (`orders.freight`):**
   * Regla: `freight >= 0.0`.
   * Rango histórico observado: `$0.02` a `$1,007.64`.
5. **Precios de Lista en Catálogo (`products.unitPrice`):**
   * Regla: `unitPrice > 0.0`.
6. **Existencias en Almacén (`products.unitsInStock`):**
   * Regla: `unitsInStock >= 0`. (El valor `0` es legítimo y representa inventario agotado).

---

## 6. Reglas Cronológicas y Lógica Temporal

1. **Secuencia de Pedido:**
   * Regla mandatoria: `orderDate <= shippedDate` (para órdenes despachadas).
   * Criterio: Un pedido nunca puede ser despachado antes de su creación.
2. **Requerimiento del Cliente:**
   * Regla mandatoria: `orderDate <= requiredDate`.
   * Criterio: La fecha exigida por el cliente debe ser igual o posterior a la emisión de la orden.
3. **Lógica de Entregas a Tiempo (KPI de Cumplimiento Logístico):**
   * `shippedDate <= requiredDate` ➔ **Pedido a Tiempo (On-Time)**.
   * `shippedDate > requiredDate` ➔ **Pedido Demorado (Delayed)** (37 pedidos históricos).
   * `shippedDate IS NULL` ➔ **Pedido Pendiente de Despacho** (21 pedidos históricos).

---

## 7. Política y Tratamiento de Valores Nulos (Estrategia para Capa Silver)

Los valores nulos identificados en la fuente no serán eliminados arbitrariamente, sino tratados según su significado de negocio:

| Tabla | Columna | % Nulos | Causa de Negocio | Tratamiento en Capa Silver |
| :--- | :--- | :--- | :--- | :--- |
| `orders` | `shippedDate` | 2.53% (21) | Pedidos no despachados / en preparación. | **Conservar como nulo (`NaT`).** No inventar fechas ficticias. Permite aislar pedidos en tránsito en Power BI. |
| `employees` | `reportsTo` | 11.11% (1) | Director General (sin superior a cargo). | **Conservar como nulo** o asignar valor `-1` para identificar la raíz de la jerarquía organizacional. |
| `customers` | `region` | 65.93% (60) | Países sin división política por estado/región. | **Imputar como `"Sin Región"`**. Evita campos vacíos en los filtros y mapas de Power BI. |
| `orders` | `shipRegion` | 61.08% (507) | Destinos internacionales sin estado regional. | **Imputar como `"Sin Región"`**. |
| `suppliers` | `region` | 68.97% (20) | Proveedores europeos o internacionales sin región. | **Imputar como `"Sin Región"`**. |
| `customers` | `postalCode` | 1.10% (1) | Dato de contacto no informado. | **Imputar como `"Sin Código"`**. |
| `orders` | `shipPostalCode` | 2.29% (19) | Destino postal no especificado. | **Imputar como `"Sin Código"`**. |
| `customers` | `fax` | 24.18% (22) | Canal de contacto opcional en desuso. | Mantener en Silver; **excluir de la Capa Gold**. |
| `suppliers` | `fax`, `homePage` | >55% (16-24) | Campos de contacto secundarios. | Mantener en Silver; **excluir de la Capa Gold**. |

---

## 8. Criterios de Aceptación para Pipelines ETL

Cualquier script de ingesta o transformación que procese datos hacia **Silver** o **Gold** debe ejecutar aserciones automatizadas basadas en este catálogo. Si un lote de datos vulnera cualquiera de estas reglas, el pipeline debe detener su ejecución y emitir una alerta de calidad de datos (*Fail-fast principle*).
