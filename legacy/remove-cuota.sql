-- this script removes "cuota approach", pretty useless tbh
UPDATE cuentas AS t
SET 
    amount = (
        SELECT SUM(c.amount)
        FROM cuentas AS c
        WHERE substr(c.description, 1, instr(c.description, 'tag: cuota') - 1)
            = substr(t.description, 1, instr(t.description, 'tag: cuota') - 1)
    ),
    description = substr(t.description, 'tag: cuota 0', '')
WHERE t.description LIKE '%tag: cuota 0';

DELETE FROM cuentas 
WHERE description REGEXP 'tag: cuota [1-9][0-9]?$';