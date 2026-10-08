# hora del primer commit 11:26:01
# Colfrance

Registro local de alertas y paradas de máquina. Django 6.1.2 y SQLite, con hora de `America/Bogota`.

## Cómo ejecutarlo

```bash
source .venv/bin/activate
python manage.py migrate
python manage.py datos_iniciales
python manage.py runserver
```

La página está en http://127.0.0.1:8000/.

## Usuarios de demostración


usuario: operarios@test.com | passs: operario123 
usuario: operarios2@test.com | passs:operario123 
usuario: supervisor@test.com | passs:supervisor123  
usuario: jefe@test.com | passs:jefe12345  

El acceso pide un correo válido. `operarios2@test.com` existe para comprobar que cada operario solo ve sus alertas.

## Qué puede hacer cada rol

- Operario: crea alertas y consulta solo las suyas.
- Supervisor: consulta y edita alertas, y registra paradas.
- Jefe: consulta alertas y paradas, y cancela una parada con motivo.

La página oculta lo que el rol no puede hacer. Cada envío vuelve a comprobar el rol en el servidor. Si no corresponde, la respuesta es 403 y no se escribe nada. El acceso exige sesión y los formularios incluyen el token CSRF.

## Comprobaciones

1. Una descripción vacía, un motivo vacío o una parada cuyo fin es igual o anterior al inicio responden 400 y no crean registros. El formulario muestra el error junto al campo. Además, la base rechaza un fin que no sea posterior al inicio.
2. La parada del Horno 3, del 08/10/2026 23:50 al 09/10/2026 00:20, muestra 30 min. La duración se calcula con las dos fechas completas y no se guarda.
3. Editar la alerta "Fuga de aceite" como operario o como jefe responde 403. Máquina, descripción, usuario y fecha quedan iguales.
4. La primera cancelación de esa parada guardó al jefe, la fecha y el motivo "Pieza reemplazada". Una segunda cancelación, con otro motivo, no cambió esos tres datos ni duplicó ni borró la fila. Operario y supervisor también reciben 403 si intentan cancelar.
5. Tras las pruebas de uso quedaron 14 alertas y 10 paradas. La página carga para los cuatro usuarios. operarios@test.com ve 8 alertas propias y ninguna de operarios2@test.com. operarios2@test.com ve solo las 6 suyas. Supervisor y jefe ven las 14 alertas y las 10 paradas.
