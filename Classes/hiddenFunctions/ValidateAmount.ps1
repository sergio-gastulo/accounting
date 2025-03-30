function ValidateAmount {
    do {
        $amount = Read-Host "`nInsert expense"
        $parsedAmount = 0.0
        if ([double]::TryParse($amount, [ref]$parsedAmount)) {
            if($parsedAmount -lt 0){
                Write-Host "`nValue must be positive."
            } else {
                break
            }
        } else {
            Write-Host "`nCould not parse '$amount' to double."
        }
    } while ($true)
    
    return $parsedAmount
}

ValidateAmount
