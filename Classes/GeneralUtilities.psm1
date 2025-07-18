class GeneralUtilities {

    static [int] ValidateInteger([string] $validation, [int] $lower_bound) {
        $tempInt = 0
        do {
            $temp = Read-Host "`nSelect number of $validation"
            try {
                $tempInt = [int]$temp
                if ($tempInt -gt $lower_bound) {
                    break
                } else {
                    Write-Host "`n'$validation' must be an integer greater than $lower_bound." -ForegroundColor Red
                }            
            } catch {
                Write-Host "`nCould not parse '$temp' as integer." -ForegroundColor Red
            }
        } while ($true)
        Write-Host "`n$validation parsed successfully: '$tempInt'" -ForegroundColor Green
        return $tempInt
    }

    static [object] ValidateDoubleCurrency([string] $validation, [double] $lower_bound) {
        $tempAmount = 0.0
        $currency = ""

        do {
            Write-Host "`nTo use this parser, you can do (basic arithmetic operation) (usd|eur|...|[empty])"
            $temp = Read-Host "`nSelect number of $validation"
            
            # this splits the string based on the last space
            $temp, $currency = $temp -split '\s(?=[^\s]*$)', 2
            
            if($currency -match '^[a-zA-Z]{3}$') {
                #if matches currency, return it as upper
                $currency = $currency.ToUpper()
            } elseif ($currency -match '\d+') {
                # if we picked a number, add it back to temp
                $temp += " " + $currency
                $currency = "PEN"
            } else {
                # default
                $currency = "PEN"
            }

            if ($temp -match "^[\+-].*") {
                Write-Host "`nParsing basic arithmetic operation..." -ForegroundColor Yellow
                if ($temp -match "[a-zA-Z]") {
                    Write-Host "`nParse failed, dangerous evaluation could lead to potential issues." -ForegroundColor Red
                } else {
                    $tempAmount = Invoke-Expression $temp
                    if ($tempAmount -gt $lower_bound) {
                        break
                    } else {
                        Write-Host "`n'$validation' must be an integer greater than $lower_bound." -ForegroundColor Red
                    }  
                }
            } else {
                try {
                    $tempAmount = [double]$temp
                    if ($tempAmount -gt $lower_bound) {
                        break
                    } else {
                        Write-Host "`n$tempAmount must be a positive double." -ForegroundColor Red
                    }
                }
                catch {
                    Write-Host "`nRunning this again, '$temp' could not be parsed to double" -ForegroundColor Red
                }
            }
        } while ($true)
        
        Write-Host "`n$validation parsed succesfully: '$tempAmount'" -ForegroundColor Green
        Write-Host "Currency: $currency"
        return $tempAmount, $currency
    }

    static [string] ValidateStringForCSV([string] $field) {
        $tempDescription = ''
        
        do {
            $tempDescription = Read-Host "`nType $field, no commas"
            if ($tempDescription -notmatch ',') {
                break
            }
            Write-Host "`nDescription cannot include comma (,)." -ForegroundColor Red
        } while ($true)
        Write-Host "`nSucessfull string: '$tempDescription'" -ForegroundColor Green
        return $tempDescription
    }

    static [datetime] ValidateDate() {
        $today = $tempDate = (Get-Date)

        Write-Host "`nEnter a particular date in (day) or (day month) format."
        Write-Host "`nTo select basic arithmetic, type '+n' or '-n'. This will operate as follows: Today +/- n"
        while($true){
            $period = Read-Host "`nInsert period or day arithmetic"
            
            if ($period -match "^([+-])(\d{1,4})$") {
                Write-Host "`nBasic date arithmetic chosen." -ForegroundColor Yellow
                try {
                    if ($matches[1] -eq '+') {
                        $tempDate = $today.AddDays(  [int]$matches[2])
                        break
                    } elseif ($matches[1] -eq '-') {
                        $tempDate = $today.AddDays(- [int]$matches[2])
                        break
                    }
                }
                catch {
                    Write-Host "`nSomething went wrong while evaluating." -ForegroundColor Red
                }
            } else {
                try {
                    $day, $month = $period.Split(" ")
                    if($month){
                        $tempDate = Get-Date -day $day -month $month
                    } else {
                        $tempDate = Get-Date -day $day
                    }
                    break
                } catch {
                    Write-Host "`nCould not parse '$period' as a valid date." -ForegroundColor Red
                }
            }

        }
        Write-Host "`nParse successfull: '$($tempDate.ToString("dddd, MMMM d, yyyy"))'" -ForegroundColor Green
        return $tempDate
    }

    static [object] GetJSON([string] $path) {
            
        $jsonArray = Get-Content ($path) -Raw | ConvertFrom-Json 
        $hashtable = [ordered]@{}
        $jsonArray | ForEach-Object {
            if ($_.subcategories) {
                $newHashtable = [ordered]@{}
                $_.subcategories | ForEach-Object {
                   $newHashtable[$_.key] = $_.shortname
                }
                $hashtable[$_.key] = $newHashtable
            } else {
                $hashtable[$_.key] = $_.shortname
            }
        }
        return @{
            array   =   $jsonArray 
            hash    =   $hashtable
        }
    }

    static [string] GetSQLQuery([string] $file, [hashtable] $hash) {
        
        $sqlFile = [IO.Path]::Combine((Split-Path $PSScriptRoot), "SQL", $file) 
        $query = Get-Content $sqlFile -Raw

        foreach ($key in $hash.Keys){
            $query = $query -replace "@$key", $hash[$key]
        }
        
        return $query
    }

}