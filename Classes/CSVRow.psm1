class CSVRow {
    [datetime]  $Date
    [Double]    $Amount
    [String]    $Category
    [String]    $Description 
    
    CSVRow () {
        $this.Date = $this.ValidateDate() 
        $this.Amount = $this.ValidateAmount() 
        $this.Description = $this.ValidateDescription()
        $this.Category = $this.ValidateCategory()
    }

    CSVRow([datetime]$Date, [double]$Amount, [string]$Category, [string]$Description) {
        $this.Date = $Date
        $this.Amount = $Amount
        $this.Category = $Category
        $this.Description = $Description
    }
    
    hidden [datetime] ValidateDate() {
        $tempDate = (Get-Date)
        
        while($true){
            $period = Read-Host "`nInsert (day) or (day month)"
            
            try {
                $day, $month = $period.Split(" ")
                if($month){
                    $tempDate = Get-Date -day $day -month $month
                } else {
                    $tempDate = Get-Date -day $day
                }
                break
            } catch {
                Write-Host "`nRunning this again, could not parse '$period'." -ForegroundColor Red
                $flag = Read-Host "`nUse Date=Today? (y/anything to go back)" 
                if ($flag -eq 'y') {
                    break
                }
            }
        }
        Write-Host "`nParse successfull: '$($tempDate.ToString("dddd, MMMM d, yyyy"))'" -ForegroundColor Blue
        return $tempDate
    }

    hidden [double] ValidateAmount() {
        $namount = 0.0
        do {
            $tempAmount = (Read-Host "`nInsert expense")
            try {
                $namount = [double]$tempAmount
                if ($namount -gt 0.0) {
                    break
                } else {
                    Write-Host "`n$tempAmount must be a positive integer." -ForegroundColor Red
                }
            }
            catch {
                Write-Host "`nRunning this again, $tempAmount could not be parsed to Double" -ForegroundColor Red
            }
        } while ($true)
        Write-Host "`nParse successfull: '$namount'" -ForegroundColor Blue
        return $namount
    }

    hidden [String] ValidateDescription() {
        $tempDescription = ''
        
        do {
            $tempDescription = Read-Host "`nType description, no commas"
            if ($tempDescription -notmatch ',') {
                break
            }
            Write-Host "`nDescription cannot include comma (,)." -ForegroundColor Red
        } while ($true)
        Write-Host "`n Succcessfull parse: '$tempDescription'" -ForegroundColor Blue
        return $tempDescription
    }

    hidden [String] ValidateCategory() {

        $categoryDict = [ordered]@{
    
            bl = 'BLIND'
            
            cas = [ordered]@{
                ga = 'CASA-GASTO'
                gi = 'CASA-GIFT'
            }
    
            cel = 'CELULAR'
    
            com = [ordered]@{    
                ag = 'COMIDA-AGUA'
                sa = 'COMIDA-SALIR'
                sn = 'COMIDA-SNACK'
                tr = 'COMIDA-TRAGO'
            }
                
            ed = 'EDUCATION'
    
            gi = 'GIFTS'
    
            ing = [ordered]@{
                s = 'INGRESO-SOLES'
                u = 'INGRESO-USD'
            }
    
            im = 'IMPUESTOS'
    
            pas = 'PASAJE'
    
            perdido = 'PERDIDO'
    
            personal = [ordered]@{
                f = 'PERSONAL-FIX'
                g = 'PERSONAL-GYM'
                h = 'PERSONAL-HEALTH'
                r = 'PERSONAL-REGALO'
                tall = 'PERSONAL-TALLER'
                tram = 'PERSONAL-TRAM' #TRAMITE
            }
            
            pet = 'PETS'
    
            sal = 'SALIDA'
    
            sub = 'SUBSCRIPTIONS'
    
            var = 'VARIOS'
    
            xch = [ordered]@{
                su = 'SOLES-USD'
                us = 'USD-SOLES'
            }
        }
    
        $tempCategory= ""
    
        :CategoryLoop do {
            Write-Host "["
            $categoryDict.Keys | ForEach-Object { "`t$_" } | Write-Host -Separator ",`n"
            Write-Host "]"
            $key = Read-Host "`nSelect a key from the dictionary above"
            $temp = $categoryDict[$key]        
    
            if ($temp -is [System.Collections.Specialized.OrderedDictionary]) {            
                $temp | ConvertTo-Json | Write-Host
                :subCategoryLoop do{
                    $tempSubCategory = Read-Host "`nKey belongs to Ordered Dictionary. Please select a key"
                    if($temp[$tempSubCategory]){
                        $tempCategory = $temp[$tempSubCategory]
                        break subCategoryLoop
                    } else {
                        Write-Host "`nUnrecognized subkey. Loop running again." -ForegroundColor Red
                        $temp | ConvertTo-Json | Write-Host
                    }
                }while($true)
                
                break CategoryLoop
    
            } elseif ($temp -is [string]) {
                $tempCategory = $temp
                Write-Host "`nCategory parsed succesfully: '$tempCategory'"
                break CategoryLoop
            } else {
                Write-Host "`nCould not parse '$key'. Loop running again." -ForegroundColor Red
            }
        } while($true)
    
        return $tempCategory
    }

    [String]Parse(){

        return @(
            $this.Date.ToString("dd-MM-yyyy"),
            $this.Amount,
            $this.Description,
            $this.Category
        ) -join ","

    }

    [Void]Print(){
        Write-Host @"
Date:        $($this.Date.ToString("dd-MM-yyyy"))
Amount:      $($this.Amount)
Description: $($this.Description)
Category:    $($this.Category)
"@
    }

    [CSVRow] Copy(){
        return [CSVRow]::new($this.Date, $this.Amount, $this.Category, $this.Description)
    }

}