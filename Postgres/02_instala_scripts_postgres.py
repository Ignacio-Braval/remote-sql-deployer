from distutils.log import error
import os
import logging as log
log.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',level=log.INFO,datefmt='%Y-%m-%d %H:%M:%S')
import json
import yaml
import psycopg2
import argparse
import boto3

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
        self.assume = False
        self.users = {}

    def run_sql_script(self, config):
        fatal_error_occurred = False
        cursor = None
        connection = None

        try:
            for script in config['scripts']:
                script_name = script['name']
                expected_result = script['expected_result']['message']

                log.info(f"{colors['OKGREEN']}├── Ejecutando {script_name}")
                
                parts = script_name.split('-')

                dbname = parts[2].lower()

                if dbname in self.users:
                    json_secret = self.users[dbname]

                db_host = json_secret['db_host']
                db_sid = json_secret['db_sid']
                db_username = json_secret['db_username']
                db_password = json_secret['db_password']
                db_port = json_secret['db_port']

                # log.info(f"db_host      =>=>=> {db_host} ")
                # log.info(f"db_sid       =>=>=> {db_sid} ")
                # log.info(f"db_username  =>=>=> {db_username} ")
                # log.info(f"db_password  =>=>=> {db_password} ")
                # log.info(f"db_port      =>=>=> {db_port} ")
                
                action =  parts[4]

                connection = psycopg2.connect(
                    dbname=dbname,
                    user=db_username,
                    password=db_password,
                    host=db_host,
                    port=db_port
                )

                # Disable autocommit
                connection.autocommit = False
                cursor = connection.cursor()

                # Read the SQL script
                with open(script_name, 'r') as file:
                    sql_script = file.read()

                # Execute the SQL script
                cursor.execute(sql_script)

                for notice in connection.notices:
                    
                    # Log Clean
                    resp_notice = notice.replace("NOTICE:", " ").strip()
                    # log.info(f"resp_notice {resp_notice}")

                    if action == "ANONIMO":
                        log.info("PL/SQL block executed successfully.")
                        connection.commit()
                        self.terminateConnection(connection, cursor)
                    else:
                        if resp_notice.replace(" ", "") == expected_result.replace(" ", ""):
                            log.info(f"{colors['OKGREEN']}│   └── RESULTADO CORRECTO")
                            log.info(f"{colors['OKGREEN']}│   └── Resultado Esperado => {expected_result}")
                            log.info(f"{colors['OKGREEN']}│   └── Resultado Real     => {resp_notice}")
                            log.info(f"{colors['OKGREEN']}│   └── Realizando Commit")
                            connection.commit()
                            self.terminateConnection(connection, cursor)
                        else:
                            log.info(f"{colors['FAIL']}│   └── RESULTADO INCORRECTO")
                            log.info(f"{colors['FAIL']}│   └── RESULTADO DISTINTO DEL ESPERADO")
                            # log.info(f"{colors['FAIL']}│   └── Resultado Esperado => {expected_result}")
                            # log.info(f"{colors['FAIL']}│   └── Resultado Real     => {resp_notice}")
                            log.info(f"{colors['FAIL']}│   └── ROLLBACK in progress...")
                            log.info(f"{colors['FAIL']}│   └── Terminando Instalacion...")
                            connection.rollback()
                            fatal_error_occurred = True
                            break

                if fatal_error_occurred:
                    log.info(f"{colors['FAIL']}└───────────────── Ejecucion de los scripts con Error ────────────────┘ \n")
                    break 
                else:
                    log.info(f"{colors['OKGREEN']}└───────────────── Ejecucion de los scripts Exitosa ────────────────┘ \n")

        except (Exception, psycopg2.DatabaseError) as error:
            log.info(f"{colors['FAIL']}│   └── Database error occurred:")
            log.info(f"{colors['FAIL']}│   └── {error}")
            if connection is not None:
                log.info(f"{colors['FAIL']}│   └── ROLLBACK in progress...")
                connection.rollback()
            fatal_error_occurred = True
        finally:
            if connection is not None:
                log.info(f"{colors['OKCYAN']}├── Terminando connexion")
                log.info(f"├── Cerrando Cursor")
                log.info(f"├── Cerrando connection")
                cursor.close()
                connection.close()
            if fatal_error_occurred:
                log.info(f"{colors['FAIL']}└── Fatal error occurred, script terminated.")
                exit(1)

    def terminateConnection(self, connection, cursor):
        log.info(f"{colors['OKCYAN']}├── Terminando connexion")
        if connection is not None:
            cursor.close()
            connection.close()
            log.info(f"{colors['OKCYAN']}│   └──  Cerrando Cursor")
            log.info(f"{colors['OKCYAN']}│   └──  Cerrando connection")

    def main(self):
        self.menu()
        self.get_users()
        self.get_secrets()

        config = self.load_config()
        self.run_sql_script(config)

    def get_secrets(self):

        if self.assume:
            self.session = self.assume_roles(
                os.environ.get("AWS_ACCESS_KEY_ID"),
                os.environ.get("AWS_SECRET_ACCESS_KEY"),
                "us-east-1",
                roles_list=[{"role":self.sts_role,"session":"STSBASE"},{"role":self.security_role,"session":"SECURITYACCOUNT"}]
            )
            # self.get_general_users()
            self.get_secret_values_generic()

    def get_secret_values_generic(self):
        client = self.session.client("secretsmanager",region_name="us-east-1")
        ambiente = os.environ.get('ambiente')
        postgres_user = os.environ.get('postgres_user')
        for user in self.users:
            SecretId = f"rds/{user}/{postgres_user}/{ambiente}"
            response = client.get_secret_value(SecretId=SecretId)
            secret_string = json.loads(response['SecretString'])
            self.users[user] = secret_string

    def get_users(self):
        config = self.load_config()
        for script in config['scripts']:
            script_name = script['name']
            parts = script_name.split('-')
            dbname = parts[2].lower()
            if (dbname) not in self.users:
                self.users[(dbname)] = self.users

    def menu(self):
        parser = argparse.ArgumentParser(description="comprobar deuda técnica")
        parser.add_argument('--sts_role',type=str, required=True)
        parser.add_argument('--security_role',type=str, required=True)
        parser.add_argument('--pipeline_type',type=str, required=False)
        parser.add_argument('--branch',type=str, required=True)
        parser.add_argument('--assume',action='store_true', default=False)
        
        args = parser.parse_args()
        self.pipeline_type = args.pipeline_type
        self.branch = args.branch
        self.sts_role = args.sts_role
        self.security_role = args.security_role
        self.assume = args.assume


    def assume_roles(self,access_key, secret_key, region, roles_list):
        # Create session with user credentials
        session = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            aws_session_token=os.environ.get('AWS_SESSION_TOKEN'),
            region_name=region
        )

        # Get STS client
        sts_client = session.client('sts')

        # Assume roles in order
        for role in roles_list:
            response = sts_client.assume_role(RoleArn=role.get("role"), RoleSessionName=role.get("session"))
            credentials = response['Credentials']
            session = boto3.Session(
                aws_access_key_id=credentials['AccessKeyId'],
                aws_secret_access_key=credentials['SecretAccessKey'],
                aws_session_token=credentials['SessionToken'],
                region_name=region
            )
            sts_client = session.client('sts')
        return session

    def load_config(self):
        filepath = "config.yml"
        with open(filepath, 'r') as file:
            return yaml.safe_load(file)


if __name__ == "__main__":
    instance = instalaScripts()
    instance.main()