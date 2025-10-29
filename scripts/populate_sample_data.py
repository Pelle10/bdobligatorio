from faker import Faker
fake = Faker('es_ES')
for i in range(1,51):
    ci = str(30000000 + i)
    nombre = fake.first_name()
    apellido = fake.last_name()
    email = f'{nombre.lower()}.{apellido.lower()}{i}@ucu.edu.uy'
    print(f'{ci},{nombre},{apellido},{email}')
