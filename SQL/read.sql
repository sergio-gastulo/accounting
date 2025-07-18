SELECT * 
FROM cuentas
WHERE date <= '@today'
ORDER BY date DESC
LIMIT @numberOfLines;