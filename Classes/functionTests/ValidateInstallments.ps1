function ValidateInstallments() {
    $tempInt = 0
    do {
        $temp = Read-Host "`nSelect number of installments"
        try {
            $tempInt = [int]$temp
            if ($tempInt -gt 1) {
                break
            } else {
                Write-Host "`nInstallments must be an integer greater than 1." -ForegroundColor Red
            }            
        } catch {
            Write-Host "`nCould not parse '$temp' to Integer. Running this again." -ForegroundColor Red
        }
    } while ($true)

    Write-Host "`nInstallments parsed successfully: '$tempInt'" -ForegroundColor Blue
    return $tempInt
}

ValidateInstallments