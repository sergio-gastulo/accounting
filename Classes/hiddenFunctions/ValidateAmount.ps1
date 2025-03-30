function ValidateAmount {
    $namount = 0.0
    do {
        $amount = (Read-Host "`nInsert expense")
        try {
            $namount = [double]$amount
            if ($namount -gt 0.0) {
                break
            } else {
                Write-Host "`n$amount must be a positive integer."
            }
        }
        catch {
            Write-Host "`nRunning this again, $amount could not be parsed to Double"
        }
    } while ($true)

    return $namount
}

ValidateAmount