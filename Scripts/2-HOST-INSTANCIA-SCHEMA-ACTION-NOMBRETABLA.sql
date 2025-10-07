-- 1 filas ingresadas
DECLARE
cant NUMBER := 0;

BEGIN


INSERT INTO SCHEMA.NOMBRETABLA (valor1, valor2) VALUES
	 	 (-50,'Se rebaja al 100% según arancel estipulado en el Condicionado Particular de su póliza vigente, al cual se le aplica el % del plan');
		 cant := cant + sql%rowcount;




	 dbms_output.put_line( 'filas ingresadas=' || cant);
END;