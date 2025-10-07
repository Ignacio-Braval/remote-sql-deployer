# Remote SQL Script Manager

**Repositorio:** remote-sql-script-manager  
**Descripción corta:** Valida, instala y ejecuta scripts SQL de forma remota en Oracle y PostgreSQL, integrable con pipelines CI/CD.  

## Descripción del proyecto

Este proyecto permite **validar, instalar y ejecutar scripts SQL** de manera remota en bases de datos Oracle y PostgreSQL. Está diseñado para su integración en pipelines de CI/CD, asegurando la correcta ejecución de scripts y evitando errores en entornos de producción.

### Características

- **Validación de scripts**:
  - Verifica que los nombres de los scripts cumplan un formato estándar.
  - Comprueba que no se incluyan sentencias prohibidas (blacklist).
  - Valida que el schema y la acción (INSERT, UPDATE, DELETE, SELECT, ANONIMO) correspondan al contenido del script.

- **Instalación y ejecución remota**:
  - Ejecuta scripts en múltiples hosts y bases de datos.
  - Compatible con Oracle y PostgreSQL.
  - Permite parametrización para full commit o rollback en caso de error.
  - Genera logs detallados de ejecución y resultados esperados.

- **Seguridad**:
  - Las credenciales se obtienen desde variables de entorno, evitando exposición de información sensible.
  - Configurable para limitar hosts, instancias y schemas permitidos.

### Estructura del proyecto

- valida_scripts.py 
**Valida la nomenclatura y contenido de los scripts SQL.**
- instalaScripts.py 
**Ejecuta los scripts de forma remota en Oracle/PostgreSQL.**
- config.yml 
**Configuración de scripts a ejecutar y resultados esperados.**
- Scripts/ 
**Carpeta con los scripts SQL.**
- README.md

## Funcionalidades principales

1. **Validación de scripts** (`valida_scripts.py`):
   - Verifica que los nombres de los archivos SQL cumplan con el formato esperado.
   - Detecta sentencias prohibidas o no permitidas en los scripts.
   - Asegura que los scripts contengan el `schema` y `action` correctos según su nombre.

2. **Ejecución de scripts** (`instalaScripts.py`):
   - Conexión remota a bases de datos Oracle o PostgreSQL usando credenciales almacenadas en variables de entorno.
   - Ejecuta los scripts de forma controlada, verificando resultados esperados.
   - Realiza `COMMIT` o `ROLLBACK` según el resultado de la ejecución.

3. **Configuración** (`config.yml`):
   - Define los scripts a ejecutar y los resultados esperados.
   - Permite parametrizar la ejecución en entornos de desarrollo o producción.

---

## Consideraciones de seguridad

- No se deben incluir credenciales en el repositorio. Todas las credenciales (usuarios, contraseñas, hosts, etc.) se obtienen mediante variables de entorno.
- Evita subir archivos que contengan información sensible de las bases de datos.

---

## Uso en proyectos de pipeline

Este proyecto está diseñado para integrarse en pipelines de CI/CD, permitiendo:

- Validar scripts antes de ejecutarlos en bases de datos de producción.
- Ejecutar scripts de forma remota en entornos controlados.
- Manejar errores y resultados de manera consistente para asegurar integridad de datos.
