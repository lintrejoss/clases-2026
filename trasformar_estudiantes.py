import csv



with open('estudiantes.csv', 'r') as csvfile:
    reader = csv.DictReader(csvfile)
    estudiantes = [row for row in reader]
    columnas = list(estudiantes[0].keys())  # Convierte el objeto iterable en una lista

print(type(estudiantes[0]))  # Imprime el nombre del primer estudiante
print(columnas)  # Imprime los nombres de las columnas