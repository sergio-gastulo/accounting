function ValidateAmount() {
    $namount = 0.0
    do {
        $tempAmount = (Read-Host "`nInsert expense")
        try {
            $namount = [double]$tempAmount
            if ($namount -gt 0.0) {
                break
            } else {
                Write-Host "`n$tempAmount must be a positive integer."
            }
        }
        catch {
            Write-Host "`nRunning this again, $tempAmount could not be parsed to Double"
        }
    } while ($true)

    return $namount
}

ValidateAmount
