# Medidas y columna calculada DAX para Power BI

Estas fórmulas ayudan a cumplir el requisito de tener al menos una medida DAX y una columna calculada DAX.

## Medidas DAX

```DAX
Promedio TRM = AVERAGE(registros_trm[valor])
```

```DAX
Volatilidad TRM = STDEV.P(registros_trm[valor])
```

```DAX
Cantidad Registros = COUNTROWS(registros_trm)
```

```DAX
Ultima Tasa = MAX(registros_trm[valor])
```

## Columna calculada DAX

Crear esta columna en la tabla `registros_trm`:

```DAX
Decision DAX =
VAR PromedioMoneda =
    CALCULATE(
        AVERAGE(registros_trm[valor]),
        ALLEXCEPT(registros_trm, registros_trm[id_moneda])
    )
RETURN
    IF(
        registros_trm[valor] < PromedioMoneda,
        "COMPRA",
        IF(registros_trm[valor] > PromedioMoneda, "VENTA", "MANTENER")
    )
```

Si Power BI te marca error por las comas, cambia las comas `,` por punto y coma `;`.

## Gráficas mínimas recomendadas

1. **Línea:** evolución de la TRM/tasa por fecha.
2. **Columnas:** promedio por moneda.
3. **Barras:** cantidad de registros por usuario.
4. **Dona o barras:** cantidad de decisiones por `Decision DAX`.
