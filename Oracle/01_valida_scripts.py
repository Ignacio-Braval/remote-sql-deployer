from distutils.log import error
# # from pathlib import Path
# import sys
# import argparse
import os
# import re
# import subprocess
# import boto3
# import json
# import requests
# import paramiko
import logging as log
log.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',level=log.INFO,datefmt='%Y-%m-%d %H:%M:%S')
import json
import yaml
import re

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
class validaScripts:
    def __init__(self) -> None:
        self.host = None
        self.sid = None
        self.DBuser = None
        self.DBpass = None
        self.blacklist = None

        self.allowed_host = None
        self.allowed_instance = None
        self.allowed_schema = None

    def main_process(self, config):
        log.info(f"{colors['OKGREEN']}┌─────────────────────┤ Validando Archivos ├───────────────────────┐")
        log.info(f"{colors['OKCYAN']}│")
        for script in config['scripts']:

            script_name = script['name']

            log.info(f"{colors['OKCYAN']}├── {script_name}")
            self.validate_script_name(script_name)

            if not os.path.exists(script_name):
                log.info(f"{colors['FAIL']}│   └── script {script_name} no encontrado ")
                exit(1)
            else:
                # log.info(f"{script_name} script existe ")
                with open(script_name, 'r') as scriptFile:
                    content = scriptFile.read().lower()
                    # Validacion de blacklist
                    if any(keyword in content for keyword in self.blacklist):
                        log.info(f"{colors['FAIL']}│   └── Script {script_name} Invalido")
                        log.info(f"{colors['FAIL']}│   └── Sentencia {self.blacklist} prohibida Encontrada")
                        exit(1)
                    else:
                        log.info(f"{colors['OKCYAN']}│   └── Archivo valido - Sentencias {self.blacklist} no encontradas")

            log.info(f"{colors['OKCYAN']}│")

        log.info(f"{colors['OKGREEN']}└───────────────── Validacion de los scripts Exitosa ────────────────┘ \n")

    def validate_script_name(self, script):
        pattern = r'^(\d+)-([A-Z0-9]+)-([A-Z]+)-([A-Z_]+)-(INSERT|UPDATE|DELETE|SELECT|ANONIMO)-([a-zA-Z0-9_]+)\.sql$'
        match = re.match(pattern, script)

        if not match:
            log.info(f"Nombre de script: '{script}' invalido.")
            parts = script.split('-')

            # log.info(f"{len(parts)}")
            if len(parts) != 6 or not parts[-1].endswith('.sql'):
                log.info(f"{colors['FAIL']} Error: Nombre del archivo no tiene el Formato correspondiente")
                self.exit_log()
            else:
                # Validacion pt 0 = Numeros
                if not parts[0].isdigit():
                    log.info(f"{colors['FAIL']} Error: Segmento 'Numero de script' no es numerica.")
                    self.exit_log()

                # Validacion pt 1 = HOST
                if not re.match(r'^[A-Z0-9]+$', parts[1]):
                    log.info(f"{colors['FAIL']} Error: Segmento 'host' erroneo ")
                    self.validate_bd_parts(parts, 1, "Formato Incorrecto" )
                    self.exit_log()
                # Validacion pt 2 = INSTANCIA
                if not re.match(r'^[A-Z]+$', parts[2]):
                    log.info(f"{colors['FAIL']} Error: Segmento 'instancia' erroneo ")
                    self.validate_bd_parts(parts, 2, "Formato Incorrecto" )
                    self.exit_log()
                # Validacion pt 3 = SCHEMA
                if not re.match(r'^[A-Z_]+$', parts[3]):
                    log.info(f"{colors['FAIL']} Error: Segmento 'Schema' erroneo ")
                    self.validate_bd_parts(parts, 3, "Formato Incorrecto" )
                    self.exit_log()

                # Validacion pt 4 = ACTION
                if not re.match(r'^INSERT|UPDATE|DELETE|SELECT|ANONIMO+$', parts[4]):
                    log.info(f"{colors['FAIL']} Error: Segmento 'ACTION' erroneo  ")
                    log.info(f"{colors['WARNING']} Acciones disponibles INSERT|UPDATE|DELETE|SELECT|ANONIMO ")
                    log.info(f"{colors['WARNING']} => VALOR ENCONTRADO: {parts[4]}")
                    self.exit_log()

                # Validacion pt 5 = TABLA
                if not re.match(r'^[A-Z0-9_]+$', parts[5]):
                    log.info(f"{colors['FAIL']} Error: Segmento 'TABLE' erroneo Formato Incorrecto ")
                    log.info(f"{colors['WARNING']} => VALOR ENCONTRADO: {parts[5]}")
                    self.exit_log()

        else: 
            parts = script.split('-')
            self.validate_bd_parts(parts, 1, "No disponible para despliege" )
            self.validate_bd_parts(parts, 2, "No disponible para despliege" )
            self.validate_bd_parts(parts, 3, "No disponible para despliege" )

            self.validate_schema_in_script(script, parts[3], parts[4])

    def validate_schema_in_script(self, script_name, schema, action ):
        """
            From array
            per sentence finds schema 
            if not exit 
        """
        # # Remove single-line comments
        # statement = re.sub(r'--.*', '', statement)
        # log.info(f" statement {statement}")

        result = self.extract_sql_statements_from_file(script_name)
        log.info(f"results = {result}")

        for line in result:
            # log.info(f"line = {line}")

            self.validate_schema_in_line(line.lower(), schema.lower())

            # Valida existencia del schema correspondiente (proveniente del nombre)
            if schema.lower() not in line.lower():
                log.info(f"{colors['FAIL']} Schema {schema} NO encontrado en: {line}")
                self.exit_log()
            # Valida existencia del la action correspondiente (proveniente del nombre)
            if action.lower() != "anonimo":
                if action.lower() not in line.lower():
                    log.info(f"{colors['FAIL']} Action {action} NO encontrada en: {line}")
                    self.exit_log()

        # Valida si codigo anonimo trae el schema
        if len(result) == 0:
            parts = script_name.split('-')
            if parts[4] == "ANONIMO":
                log.info(f"{colors['OKCYAN']}│   └── Script de codigo Anonimo")
                with open(script_name, 'r') as file:
                    plsql_code = file.read()
                    plsql_code = plsql_code.replace('\r\n', '\n')
                    pattern = rf'\b{re.escape(schema)}\b'

                    if not re.search(pattern, plsql_code, re.IGNORECASE):
                        log.info(f"{colors['FAIL']} Schema '{schema}' No existe en el script")
                        self.exit_log()

    def validate_schema_in_line(self, line, schema):
        line = line.replace('\r\n', '\n')
        sql_pattern = re.compile(r'\b(SELECT\b.+?;|INSERT INTO\b.+?;|UPDATE\b.+?;|DELETE FROM\b.+?;)', re.IGNORECASE | re.DOTALL)
        sql_statements = sql_pattern.findall(line)
        # log.info(f"sql_statements = {sql_statements}")
        for statement in sql_statements:
            schema_present, message = self.validate_specific_schema_in_sql(statement, schema)
            if not schema_present:
                # log.info(f"statement => {statement}")
                # log.info(f"{colors['FAIL']} Schema_present, message {schema_present} , {message}")
                # log.info(f"{colors['FAIL']} Schema '{schema}' No existe en el script")
                log.info(f"{colors['FAIL']} Error con el script {message}")
                self.exit_log()

    def validate_specific_schema_in_sql(self, statement, schema):        
        statement_lower = statement.lower()
        
        if 'insert into' in statement_lower:
            table_part = statement_lower.split('into')[1].strip()
            table_name = table_part.split('(')[0].strip()
        elif 'update' in statement_lower:
            table_part = statement_lower.split('update')[1].strip()
            table_name = table_part.split('set')[0].strip()
        elif 'delete from' in statement_lower:
            table_part = statement_lower.split('from')[1].strip()
            table_name = table_part.split(' ')[0].strip()
        else:
            return False, "Unsupported SQL statement"
        
        table_name = table_name.strip('`"')  # Clean the table name
        
        if table_name.startswith(f"{schema.lower()}."):
            return True, f"Schema '{schema}' found in statement: {statement}"
        else:
            return False, f"Schema '{schema}' not found in statement: {statement}"

    def extract_sql_statements_from_file(self, file_path):
        """
        Reads the file, looks for SQL sentences, and stores them in an array.
        Ignores comments starting with '--'.
        """
        try:
            with open(file_path, 'r') as file:
                plsql_code = file.read()
                
                plsql_code = plsql_code.replace('\r\n', '\n')
                # Remove single-line comments
                plsql_code = re.sub(r'--.*', '', plsql_code)
                # Define regex pattern for SQL statements
                sql_pattern = re.compile(
                    r'\b(SELECT\b.+?;|INSERT INTO\b.+?;|UPDATE\b.+?;|DELETE FROM\b.+?;)',
                    re.IGNORECASE | re.DOTALL
                )

                # Extract SQL statements
                sql_statements = sql_pattern.findall(plsql_code)

                # Clean whitespace in statements
                cleaned_statements = [re.sub(r'\s+', ' ', stmt.strip()) for stmt in sql_statements]

                return cleaned_statements

        except FileNotFoundError:
            log.info(f"The file {file_path} was not found.")
            return []

    def main(self):
        self.menu()
        config = self.load_config()
        self.main_process(config)
        # exit(1)

    def load_config(self):
        filepath = "config.yml"
        try:
            # log.info(f"Loading configuration from {filepath}")
            with open(filepath, 'r') as file:
                config = yaml.safe_load(file)
            # log.info("Configuration loaded successfully")
            return config
        except yaml.parser.ParserError as e:
            self.log_yaml_error(filepath, e)
            exit(1)
        except Exception as e:
            log.error(f"Unexpected error: {e}")
            exit(1)
    
    def log_yaml_error(self, filepath, error):
        with open(filepath, 'r') as file:
            lines = file.readlines()
        
        log.error(f"{colors['FAIL']} Error de Indentacion en el Archivo {filepath}: {error}")
        error_line = error.problem_mark.line
        error_column = error.problem_mark.column
        context_lines = 5  # lineas a mostrar
        
        start = max(0, error_line - context_lines)
        end = min(len(lines), error_line + context_lines + 1)
        
        log.error("")
        log.error("┌───────────────────────────┤ config.yml ├───────────────────────────┐ ")
        for i in range(start, end):
            line_indicator = f"{colors['WARNING']}>" if i == error_line else " "
            log.error(f"{line_indicator} Line {i + 1:4}: {lines[i].rstrip()}")
        log.info("└─────────────────────────────────────────────────────────────────────┘ \n")
        log.error(f"{colors['FAIL']} El Error esta en la linea: {error_line + 1}, columna {error_column + 1}")
        log.error(f"{colors['FAIL']} Favor revisar {filepath}")

    def exit_log(self):
        log.error(f"\n")
        log.error(f"{colors['OKCYAN']} ┌───────────────────────────┤ Validacion terminada ├───────────────────────────┐ ")
        log.error(f"{colors['OKCYAN']} │ Para mas informacion Visitar:")
        log.error(f"{colors['OKCYAN']} │ https://cnsv.atlassian.net/wiki/spaces/DEV/pages/297599466/DATOS-QA")
        log.error(f"{colors['OKCYAN']} └──────────────────────────────────────────────────────────────────────────────┘")
        exit(1)

    def validate_bd_parts(self, parts, position, message):
            # log.info(f"Validando {parts}")
            # log.info(f"Validando {parts[position]}")
            if position == 1:
                # log.info(f"Validando HOST")
                if parts[position] not in self.allowed_host:
                    log.info(f"{colors['FAIL']} {parts[position]} {message}")
                    log.info(f"{colors['WARNING']} Valores disponible {self.allowed_host}")
                    exit(1)
            if position == 2:
                # log.info(f"{colors['FAIL']} Validando INSTANCIA")
                if parts[position] not in self.allowed_instance:
                    log.info(f"{colors['FAIL']} {parts[position]} {message}")
                    log.info(f"{colors['WARNING']} Valores disponible {self.allowed_instance}")
                    exit(1)
            if position == 3:
                # log.info(f"{colors['FAIL']} Validando SCHEMA")
                if parts[position] not in self.allowed_schema:
                    log.info(f"{colors['FAIL']} {parts[position]} {message}")
                    log.info(f"{colors['WARNING']} Valores disponible {self.allowed_schema}")
                    exit(1)

    def menu(self):
        self.allowed_host = os.environ.get("allowed_host_oracle").split(", ")
        self.allowed_instance = os.environ.get("allowed_instance_oracle").split(", ")
        self.allowed_schema = os.environ.get("allowed_schema_oracle").split(", ")
        self.blacklist = os.environ.get("blacklist_sentence").split(", ")

if __name__ == "__main__":
    instance = validaScripts()
    instance.main()