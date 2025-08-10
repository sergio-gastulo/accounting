SELECT * 
FROM cuentas
WHERE date <= '@today'
ORDER BY 
    date DESC,
    amount DESC
LIMIT @numberOfLines;