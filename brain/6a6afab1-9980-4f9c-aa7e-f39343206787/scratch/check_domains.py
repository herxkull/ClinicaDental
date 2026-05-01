from clientes.models import Clinica, Dominio
c = Clinica.objects.filter(schema_name='roeden').first()
print(f'Clinica: {c}')
if c:
    doms = [d.domain for d in Dominio.objects.filter(tenant=c)]
    print(f'Dominios: {doms}')
else:
    print('Clinica no encontrada')
