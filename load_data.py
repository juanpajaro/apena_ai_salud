import pandas as pd

def load_data(file_path):
    """
    Load data from a CSV file into a pandas DataFrame.

    Parameters:
    - file_path (str): The path to the CSV file.

    Returns:
    - pd.DataFrame: A DataFrame containing the loaded data.
    """
    encoding_type = 'latin1'  # Adjust encoding as necessary
    df = pd.read_csv(file_path, nrows=100000, sep="|", encoding=encoding_type)  # Limiting to first 1000 rows for performance    
    return df

#guardar las columnas en un archivo de texto
def save_columns_to_file(columns, file_name):
    with open(file_name, 'w') as f:
        for column in columns:
            f.write(f"{column}\n")

#seleccionar las columnas que se van a usar
def select_columns(data, columns):
    return data[columns]

#guardar el conjunto de datos filtrado en un nuevo archivo csv
def save_filtered_data(data, file_name):
    data.to_csv(file_name, index=False)

if __name__ == "__main__":
    data = load_data("CaobaApneaSueno.txt")
    #print(data.info())
    #columnas = list(data.columns)
    #print(columnas)
    #save_columns_to_file(columnas, "columnas.txt")
    #columnas_seleccionadas = ["FinalidadConsulta", "CondicionUsuaria", "NombreDx", "EstadoGeneral", "MotivodeConsulta", "EnfermedadActual", "Apnea"]
    columnas_seleccionadas = ["EnfermedadActual", "Apnea"]
    data_seleccionada = select_columns(data, columnas_seleccionadas)
    print(data_seleccionada.head())
    save_filtered_data(data_seleccionada, "datos_apnea.csv")
