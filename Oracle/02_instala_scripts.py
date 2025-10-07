from distutils.log import error
import os
import logging as log
log.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',level=log.INFO,datefmt='%Y-%m-%d %H:%M:%S')
import cx_Oracle
import json
import yaml

colors={
        "HEADER": '\033[95m',
        "OKBLUE": '\033[94m',
        "OKCYAN": '\033[96m',
        "OKGREEN": '\033[92m',
        "WARNING": '\033[93m',
        "FAIL": '\033[91m',
        "ENDC": '\033[0m',
        "BOLD": '\033[1m',
        "UNDERLINE": '\033[4m'
}
class instalaScripts:
    def __init__(self) -> None:
        self.DBuser = None
        self.DBpass = None
        self.parametrizacion = "no"

    def run_sql_script(self, config):
        log.info(f"{colors['OKGREEN']}┌─────────────────────┤ Ejecutando scripts ├───────────────────────┐")
        fatal_error_occurred = False
        cursor = None
        connection = None

        try:
            for script in config['scripts']:
                script_name = script['name']
                expected_result = script['expected_result']['message']

                parts = script_name.split('-')
                host = parts[1] 
                instance = parts[2] 
                action =  parts[4]
                ####################################################

                dsn = self.define_dsn(host, instance)

                connection = cx_Oracle.connect(user=self.DBuser, password=self.DBpass, dsn=dsn)

                connection.autocommit = False  # Default is False, set to True for autocommit

                cursor = connection.cursor()
                cursor.callproc("dbms_output.enable")

                ####################################################

                log.info(f"{colors['OKCYAN']}├── Ejecutando {script_name}")

                with open(script_name, 'r') as file:
                    plsql_script = file.read()

                cursor.execute(plsql_script)

                statusVar = cursor.var(cx_Oracle.NUMBER)
                lineVar = cursor.var(cx_Oracle.STRING)
                # log.info(f"statusVar {statusVar}")
                # log.info(f"lineVar {lineVar}")
                while True:
                    cursor.callproc("dbms_output.get_line", (lineVar, statusVar))
                    if action == "ANONIMO":
                        log.info("PL/SQL block executed successfully.")
                        connection.commit()

                    if statusVar.getvalue() == 1:  # Indicates there is no more output, if anon breaks
                        break

                    # if not action == "ANONIMO":
                    if lineVar.getvalue().replace(" ", "") == expected_result.replace(" ", ""):
                        log.info(f"{colors['OKGREEN']}│   └── RESULTADO CORRECTO")
                        log.info(f"{colors['OKGREEN']}│   └── Resultado Esperado => {expected_result}")
                        log.info(f"{colors['OKGREEN']}│   └── Resultado Real     => {lineVar.getvalue()}")
                        log.info(f"{colors['OKGREEN']}│   └── Realizando Commit")
                        connection.commit()
                    else:
                        log.info(f"{colors['FAIL']}│   └── RESULTADO INCORRECTO")
                        log.info(f"{colors['FAIL']}│   └── RESULTADO DISTINTO DEL ESPERADO")
                        # log.info(f"{colors['FAIL']}│   └── Resultado Esperado => {expected_result}")
                        # log.info(f"{colors['FAIL']}│   └── Resultado Real     => {lineVar.getvalue()}")
                        log.info(f"{colors['FAIL']}│   └── ROLLBACK in progress...")
                        log.info(f"{colors['FAIL']}│   └── Terminando Instalacion...")
                        log.info(f"{colors['FAIL']}│   └──────────────────────────────────────────────────────┘")
                        connection.rollback()
                        fatal_error_occurred = True
                        break

                if fatal_error_occurred:
                    log.info(f"{colors['FAIL']}└───────────────── Ejecucion de los scripts con Error ────────────────┘ \n")
                    break 
                else:
                    log.info(f"{colors['OKGREEN']}└───────────────── Ejecucion de los scripts Exitosa ────────────────┘ \n")

        except cx_Oracle.DatabaseError as error:
            log.info(f"{colors['FAIL']}│   └── Database error occurred:")
            log.info(f"{colors['FAIL']}│   └── {error}")
            # Rollback in case of error
            if connection is not None:  # Ensure connection was successfully made
                log.info(f"{colors['FAIL']}│   └── ROLLBACK in progress...")
                connection.rollback()
            fatal_error_occurred = True

        finally:
            if 'cursor' in locals() and cursor is not None:
                log.info(f"│   └── Cerrando Cursor")
                cursor.close()
            if 'connection' in locals() and connection is not None:
                log.info(f"│   └── Cerrando connection")
                connection.close()
            if fatal_error_occurred:
                log.info(f"{colors['FAIL']}│   └── Fatal error occurred, script terminated.")
                exit(1)

    def run_sql_script_parametrizacion(self, config):
        log.info(f"{colors['OKGREEN']}┌─────────────────────┤ Ejecutando scripts ├───────────────────────┐")
        fatal_error_occurred = False
        connections = {}
        cursors = {}

        try:
            for script in config['scripts']:
                script_name = script['name']
                parts = script_name.split('-')
                host = parts[1]
                instance = parts[2]

                if (host, instance) not in connections:
                    dsn = self.define_dsn(host, instance)
                    connection = cx_Oracle.connect(user=self.DBuser, password=self.DBpass, dsn=dsn)
                    connection.autocommit = False
                    cursor = connection.cursor()
                    cursor.callproc("dbms_output.enable")
                    
                    # guarda en arreglo la conexion y cursor
                    connections[(host, instance)] = connection
                    cursors[(host, instance)] = cursor

            for script in config['scripts']:
                script_name = script['name']
                expected_result = script['expected_result']['message']
                parts = script_name.split('-')
                host = parts[1]
                instance = parts[2]
                action = parts[4]

                connection = connections[(host, instance)]
                cursor = cursors[(host, instance)]

                log.info(f"{colors['OKCYAN']}├── Ejecutando {script_name}")

                with open(script_name, 'r') as file:
                    plsql_script = file.read()

                cursor.execute(plsql_script)

                statusVar = cursor.var(cx_Oracle.NUMBER)
                lineVar = cursor.var(cx_Oracle.STRING)

                while True:
                    cursor.callproc("dbms_output.get_line", (lineVar, statusVar))

                    if action == "ANONIMO":
                        log.info("PL/SQL block executed successfully.")

                    if statusVar.getvalue() == 1:
                        break

                    if not action == "ANONIMO":
                        if lineVar.getvalue().replace(" ", "") == expected_result.replace(" ", ""):
                            log.info(f"{colors['OKGREEN']}│   └── RESULTADO CORRECTO")
                            log.info(f"{colors['OKGREEN']}│   └── Resultado Esperado => {expected_result}")
                            log.info(f"{colors['OKGREEN']}│   └── Resultado Real     => {lineVar.getvalue()}")

                        else:
                            log.info(f"{colors['FAIL']}│   └── RESULTADO INCORRECTO")
                            log.info(f"{colors['FAIL']}│   └── RESULTADO DISTINTO DEL ESPERADO")
                            log.info(f"{colors['FAIL']}│   └── Se ejecuta ROLLBACK")
                            log.info(f"{colors['FAIL']}│   └── Terminando Instalacion...")
                            fatal_error_occurred = True
                            break

                if fatal_error_occurred:
                    log.info(f"{colors['FAIL']}└───────────────── Ejecucion de script con Error ────────────────┘ \n")
                    break
                else:
                    log.info(f"{colors['OKGREEN']}└───────────────── Ejecucion de script Exitosa ────────────────┘ \n")

            if not fatal_error_occurred:
                log.info(f"{colors['OKCYAN']}┌────────────────────┤ COMMIT ├────────────────────┐ ")
                for (host, instance), connection in connections.items():
                    log.info(f"{colors['OKCYAN']}│   └── Realizando Commit final en {host}-{instance}")
                    connection.commit()
                log.info(f"{colors['OKCYAN']}└────────────────────────────────────────────────────┘ ")
            else:
                log.info(f"{colors['WARNING']}┌────────────────────┤ ROLLBACK ├────────────────────┐ ")
                for (host, instance), connection in connections.items():
                    log.info(f"{colors['WARNING']}│   └── Realizando Rollback en {host}-{instance}")
                    connection.rollback()
                log.info(f"{colors['WARNING']}└────────────────────────────────────────────────────┘ ")

        except cx_Oracle.DatabaseError as error:
            log.info(f"│   └── Database error occurred:")
            log.info(f"│   └── {error}")
            if connections:
                for (host, instance), connection in connections.items():
                    log.info(f"│   └── ROLLBACK in progress for {host}-{instance}...")
                    connection.rollback()
            fatal_error_occurred = True

        finally:
            log.info(f"{colors['OKCYAN']}┌─────────────── Terminando conexion ───────────────┐ ")
            for (host, instance), cursor in cursors.items():
                if cursor:
                    log.info(f"{colors['OKCYAN']}│   └── Cerrando Cursor para {host}-{instance}")
                    cursor.close()
            for (host, instance), connection in connections.items():
                if connection:
                    log.info(f"{colors['OKCYAN']}│   └── Cerrando connection para {host}-{instance}")
                    connection.close()
            log.info(f"{colors['OKCYAN']}└───────────────────────────────────────────────────┘ ")

            if fatal_error_occurred:
                log.info(f"{colors['FAIL']} ────────── Error Fatal, script terminados ────────── ")
                exit(1)

    def terminateConnection(self, connection, cursor):
        log.info(f"{colors['OKCYAN']}├── Terminando connexion")
        if connection is not None:
            cursor.close()
            connection.close()
            log.info(f"{colors['OKCYAN']}│   └──  Cerrando Cursor")
            log.info(f"{colors['OKCYAN']}│   └──  Cerrando connection")

    def validate_output_logs(self, resultados_esperados, bd_output):
        '''
            param1: lista de resultados esperados desde el config.yml
            param2: la linea de log de bd
        '''

        found = False

        for expected_result in resultados_esperados:
            if bd_output.replace(" ", "") == expected_result.replace(" ", ""):
                found = True
                return bd_output

        if not found:
            return found

    def define_dsn(self, host, instance):
        if host == "TERIDANUS":
            # log.info(f"{colors['OKGREEN']} desplegando en TERIDAMUS")
            dsn = cx_Oracle.makedsn(f'{host}.cnsv.cl', "1521", service_name=f'{instance}')

        if host == "TCONVM224":
            # log.info(f"{colors['OKGREEN']} desplegando en TCONVM224")
            dsn = cx_Oracle.makedsn(host=f"{host}.cnsv.cl", port=1521, sid=f'{instance}')

        if host == "TCON118":
            # log.info(f"{colors['OKGREEN']} desplegando en TCON118")
            dsn = cx_Oracle.makedsn(f'{host}.cnsv.cl', "1521", service_name=f'{instance}')
        # self.allowed_host = ['TERIDANUS', 'TCONVM224', 'C6ME0004', 'TCON118']

        if host == "C6ME0005":
            # log.info(f"{colors['OKGREEN']} desplegando en C6ME0005")
            dsn = cx_Oracle.makedsn(f'{host}.cnsv.cl', "1521", service_name=f'{instance}')

        return dsn

    def main(self):
        self.menu()
        config = self.load_config()

        # valida si es parametrizacion para full commit
        if self.parametrizacion == "si":
            self.run_sql_script_parametrizacion(config)
        else:
            self.run_sql_script(config)
            

    def load_config(self):
        filepath = "config.yml"
        with open(filepath, 'r') as file:
            return yaml.safe_load(file)

    def menu(self):
        self.parametrizacion = os.environ.get("parametrizacion")
        self.DBuser = os.environ.get("DBuser_oracle")
        self.DBpass = os.environ.get("DBpass_oracle")

if __name__ == "__main__":
    instance = instalaScripts()
    instance.main()