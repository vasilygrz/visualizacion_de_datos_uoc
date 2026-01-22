# Análisis de la transferencia de armamento pesado a Ucrania

## Descripción

Esta es una *web app* creada con Python y Streamlit para analizar la importación y transferencia de armamento pesado a Ucrania en dos períodos; antes (2014-2021) y después (2022-2024) de la invasión rusa de febrero de 2022. Para ello, se utilizado la base de datos [**Arms Transfers**](https://www.sipri.org/databases/armstransfers) del Stockholm International Peace Research Institute (SIPRI). Los datos del año 2025 no están disponibles debido a que se publican en marzo del año siguiente.

El armamento pesado son las armas pesadas son máquinas de mayor tamaño que pueden utilizarse en combate inmediato e integrar diversas necesidades militares (movimiento, potencia de fuego, etc.) en un único sistema.

Enlace: <https://ukrainearms.streamlit.app/>

## Licencia

Los [términos de uso](https://www.sipri.org/about/terms-and-conditions) del SIPRI permiten:

- utilizar sus datos para fines no comerciales, citando la fuente; y
- reproducir hasta el 10% de la base de datos en cuestión.

El código fuente se publica bajo la licencia GPLv3.

## Datos

En el directorio `data` se encuentran los datos procesados en formato Parquet.

1. `trade_register_processed.parquet` contiene las transferencias de armamento pesado a Ucrania desde 2014 hasta 2024. Se realizaron las siguientes transformaciones:

   - Se agruparon las 57 categorías originales de armas pesadas en 11 categorías principales (`Weapon category`).
   - Se asociaron los países con sus respectivas capitales (`Supplier capital`) y coordenadas geográficas (`capital_lat`, `capital_lon`).
   - Se asociaron manualmente las armas con sus fabricantes (`Company`) y países de origen (`Country of origin`). Este enfoque presenta una limitación: los antiguos países comunistas han heredado armamento soviético fabricado por empresas que ahora pertenecen a países independientes, por lo que la compañía estatal rusa Rostec está sobrerrepresentada.

   El esquema de los datos es el siguiente:

    ```text
    <class 'pandas.core.frame.DataFrame'>
    RangeIndex: 415 entries, 0 to 414
    Data columns (total 13 columns):
     #   Column                          Non-Null Count  Dtype  
    ---  ------                          --------------  -----  
     0   Recipient                       415 non-null    object 
     1   Supplier                        415 non-null    object 
     2   Supplier capital                415 non-null    object 
     3   capital_lat                     415 non-null    float64
     4   capital_lon                     415 non-null    float64
     5   Delivery number                 415 non-null    int64  
     6   Delivery year start             415 non-null    int64  
     7   Delivery year end               415 non-null    int64  
     8   Weapon designation              415 non-null    object 
     9   Weapon category                 415 non-null    object 
     10  Company                         385 non-null    object 
     11  Country of origin               403 non-null    object 
     12  SIPRI TIV of delivered weapons  415 non-null    float64
    dtypes: float64(3), int64(3), object(7)
    memory usage: 42.3+ KB
    ```

2. `ukraine_importer_rank_by_period.parquet` contiene la posición de Ucrania como país importador y el porcentaje que representa sobre el total mundial de importaciones en los períodos 2014-2021 y 2022-2024.

    El esquema de los datos es el siguiente:

    ```text
    <class 'pandas.core.frame.DataFrame'>
    RangeIndex: 2 entries, 0 to 1
    Data columns (total 5 columns):
     #   Column                        Non-Null Count  Dtype  
    ---  ------                        --------------  -----  
     0   Recipient                     2 non-null      object 
     1   Period                        2 non-null      object 
     2   Rank                          2 non-null      float64
     3   TIV                           2 non-null      float64
     4   Share of global arms imports  2 non-null      float64
    dtypes: float64(3), object(2)
    memory usage: 212.0+ bytes
    ```

## Software

Se ha empleado el siguiente *software*:

- **Lenguaje de programación**: Python 3.13.
- **Procesamiento**: pandas, numpy.
- **Visualización**: PyDeck (mapa), Plotly (gráficos de barras).
- ***Web app***: Streamlit.
