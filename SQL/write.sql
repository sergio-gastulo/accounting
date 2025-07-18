INSERT INTO cuentas 
    (date, amount, description, category, currency) 
VALUES 
    ('@date', @amount, '@description', '@category', '@currency');