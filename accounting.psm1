#   Getting the date

while ($true) {
    try {
        $dayNumber = [int](Read-Host "`nWrite the day")
        Write-Host "`nParse successful." -ForegroundColor Green
        Write-Host $dayNumber
        if (($dayNumber -gt 31) -or ($dayNumber -lt 1)){
            Write-Host "`nHowever, it must be a positive integer < 31" -ForegroundColor Red
        } else {
            break
        }
    }
    catch {
        Write-Host "`nUps, something wrong happened while parsing. `nTry again`n" -ForegroundColor Red
    }
}

$day = "{0:D2}" -f $dayNumber
$period = (Get-Date -Format 'MM-yyyy')
$date = "$day-$period"

Write-Host "`nParsed date: $date" -ForegroundColor Blue

#   Register the amount spent
do {
    $monto = Read-Host "`nEnter the amount spent"
    $isValid = [double]::TryParse($monto, [ref]$null)
    if (-not $isValid) {
        Write-Host "Invalid input. The amount spent must be a positive real." -ForegroundColor Red
    }
} while (-not $isValid)
$monto = [double]$monto

Write-Host "`nValid! Please move onto the next step`n" -ForegroundColor Green

# Loading dictionary
$categoryDict = @{
    bl      =   'BLIND'
    cas     =   'CASA'
    cel     =   'CELULAR'
    cvar    =   'COM_VAR'
    ing     =   'INGRESO'
    men     =   'MENU'
    pas     =   'PASAJE'
    per     =   'PERSONAL'
    rec     =   'RECIBO'
    usd     =   'USD_INC'
    var     =   'VARIOS'
}

# Printing category list for reference
$categoryDict | ConvertTo-Json -Depth 2

do {
    $key = Read-Host "`nSelect a key from the dictionary above"
    if ($categoryDict.ContainsKey($key)) {
        $category = $categoryDict[$key]
        break
    } else {
        Write-Host "`nInvalid key, please try again." -ForegroundColor Red
    }
} while ($true)
Write-Host "`nValid! Please move onto the next step" -ForegroundColor Green

# Amount spent description
do {
    $description = Read-Host "`nType description. No commas, and no 'enhe'"
    if ($description -notmatch ',') {
        # At this moment, we can't prevent ñ from being prompted here.
        # We trust on our user.
        # bug known at enhe_is_not_detected_from_console....ps1
        break
    }
    Write-Host "`nDescription must not include 'enhe' or comma (,)" -ForegroundColor Red
} while ($true)
Write-Host "`nValid! Please move onto the next step" -ForegroundColor Green

#   The path of the csv file
$paths = 'C:\Users\sgast\documents_personal\excel\cuentas.csv'

# What happens if the amount spent is greater than 200
if (($monto -gt 200) -and -not ($category -in @("BLIND","INGRESO","USD_INC"))) {
    
    $numMonths  =   Read-Host "`nPlease add how many months you want to split your data."
    $newMonto   =   ($monto)/([int]$numMonths)
    $temp       =   [int](($date -split '-')[1])
    
    for ($i = 0; $i -lt $numMonths; $i++) {
        $newDay            =   "{0:D2}" -f ($temp + $i) 
        $newDate           =   [string]($date -replace '-\d{2}-', "-$newDay-")        
        $newDescription    =   "$description tag: cuota $i"
        
        #   The row to be append on the csv file
        $value = "$newDate,$newMonto,$newDescription,$category"
        add-content -path $paths -value "$value"
    }
} else {
    $value = "$date,$monto,$description,$category"
    add-content -path $paths -value "$value"
}