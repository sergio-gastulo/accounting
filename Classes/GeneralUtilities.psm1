class GeneralUtilities {
    static [int] ValidateInteger([string] $validation, [int] $lowerBound) {
        $tempInt = 0
        while ($true) {
            $temp = Read-Host "`nSelect number of $validation"

            # parsing
            if (-not [int]::TryParse($temp, [ref]$tempInt)) {
                Write-Host "`nCould not parse '$temp' as integer." -ForegroundColor Red
                continue
            }

            # checking bounds
            if ($tempInt -le $lowerBound) {
                Write-Host "`n'$validation' must be an integer greater than $lowerBound." -ForegroundColor Red
                continue
            }

            # if we're here, valid integer
            Write-Host "`n'$validation' parsed successfully: '$tempInt'" -ForegroundColor Green
            break
        }
        return $tempInt
    }


    static [double] ValidateDoubleArithmeticOperation([string] $validation, [double] $lowerBound, [string] $operation = ""){
        $tempDouble = 0.0
        $validateOperation = {
            param([string] $operation)
            $doubleVar = 0.0

            # does $operation start with '=' or '+' or '-'?
            if ($operation -match "^[=\+-].*"){
                Write-Host "`nParsing double operation."
            }
            # if it doesn't, user is probably trying to pass a double.
            else {
                Write-Host "`nParsing basic double number."
                if(-not [double]::TryParse($operation, [ref]$doubleVar)) {
                    Write-Host  "`nCould not parse '$operation' as double." -ForegroundColor Red
                    throw
                }
            }

            # catching injections
            if ($operation -match "[a-zA-Z]") {
                Write-Host "`nParse failed, dangerous evaluation could lead to potential issues." -ForegroundColor Red
                throw
            }

            # if we're here, wether it's double or an arithmetic operation
            $doubleVar = [double](Invoke-Expression ($operation).Replace("=",""))

            #if parse successfull, check bounds:
            if ($doubleVar -le $lowerBound) {
                Write-Host "'$doubleVar' must be greater than '$lowerBound'"
                throw
            }

            # here: completely valid double
            Write-Host "`nParsed successfully: '$doubleVar'" -ForegroundColor Green
            return [double]$doubleVar

        }

        while ($true) {
            try {
                if (-not $operation) {
                    Write-Host "`nTo use this parser, you can type a number or use basic arithmetic."
                    Write-Host "Example: '=1+1' parses to '2'. Must start with '='."
                    $operation = Read-Host "`nWrite here '$validation'"
                }
                $tempDouble = $validateOperation.Invoke($operation)[0]
                break
            }
            catch {
                Write-Host "`n'$operation' could not be parsed."
                # forcing prompt
                $operation = $null
            }
        }

        return [double]$tempDouble
    }


    static [string] ValidateCurrency([string]$currency = "") {
        $tempCurr = ""
        $defaultCurr = "PEN"
        $validateCurr = {
            param($curr)
            # check if length = 3
            if ($curr.length -eq 0) {
                Write-Host "Defaulting to default currency: '$defaultCurr'"
                $curr = $defaultCurr 
            } elseif (-not $curr.Length -eq 3) {
                Write-Host "'$curr' is not a valid currency as per ISO convention: https://en.wikipedia.org/wiki/ISO_4217"
                throw                 
            }
            # return in uppercase
            return $curr.ToUpper()
        }

        while ($true) {
            if (-not $currency) {
                Write-Host "`nValidation of currency. Remember that a valid currency has string length = 3."
                $currency = Read-Host "Write your currency here"
            }
            try {
                $tempCurr = $validateCurr.Invoke($currency)[0]
                break
            }
            catch {
                Write-Host "'$currency' could not be parsed as a valid currency."
                $currency = $null
            }
        }        
        return $tempCurr
    }

    static [object] ValidateDoubleCurrency([string] $validation) {
        $lowerBound = 0.0 # money should always be positive
        $tempAmount = 0.0
        $currency = ""

        do {
            Write-Host "`nTo use this parser, you can do (basic arithmetic operation) (usd|eur|...|[empty for default currency])"
            $temp = Read-Host "Select number of $validation"
            
            # this splits the string based on the last space
            $temp, $currency = $temp -split '\s(?=[^\s]*$)', 2

            # if we picked a number, append it back to $temp
            if($currency -match "\d+") {
                $temp += $currency
            }
            try {
                $tempAmount = [GeneralUtilities]::ValidateDoubleArithmeticOperation("Amount", $lowerBound, $temp)
                $currency = [GeneralUtilities]::ValidateCurrency($currency)
                break
            }
            catch {
                Write-Host "Something went wrong while parsing."
            }
        } while ($true)
        
        Write-Host "$validation parsed succesfully: '$tempAmount'" -ForegroundColor Green
        Write-Host "Currency: $currency" -ForegroundColor Green
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


    # only God knows how this works
    static [string] ValidateCategory([System.Collections.Specialized.OrderedDictionary] $categoryDict) {
    
        $tempCategory= ""
    
        :CategoryLoop do {
            Write-Host "["
            
            $categoryDict.Keys | ForEach-Object { 
                $temporaryValueOfCategoryDict = $categoryDict[$_]
                if ($temporaryValueOfCategoryDict -is [string]) {
                    $valueStringToPrint = ": `t$temporaryValueOfCategoryDict,"
                } else {
                    $valueStringToPrint = ","
                }
                Write-Host "`t$_$valueStringToPrint" 
            }
            
            Write-Host "]"
            $key = Read-Host "`nSelect a key from the dictionary above"
            $temp = $categoryDict[$key]        
    
            if ($temp -is [System.Collections.Specialized.OrderedDictionary]) {      
                Write-Host "`n"      
                $temp | ConvertTo-Json | Write-Host
                :subCategoryLoop do {
                    $tempSubCategory = Read-Host "`nKey belongs to Ordered Dictionary. Please select a key"
                    if($temp[$tempSubCategory]){
                        $tempCategory = $temp[$tempSubCategory]
                        break subCategoryLoop
                    } else {
                        Write-Host "`nUnrecognized subkey. Loop running again." -ForegroundColor Red
                        Write-Host "`n"
                        $temp | ConvertTo-Json | Write-Host
                    }
                } while($true)
                
                break CategoryLoop
    
            } elseif ($temp -is [string]) {
                $tempCategory = $temp
                Write-Host "`nCategory parsed succesfully: '$tempCategory'" -ForegroundColor Green
                break CategoryLoop
            } else {
                Write-Host "`nCould not parse '$key'. Loop running again." -ForegroundColor Red
            }
        } while($true)
    
        return $tempCategory
    }

}
