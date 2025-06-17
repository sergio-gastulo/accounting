class CSVRow {
    [datetime]  $Date
    [Double]    $Amount
    [String]    $Category
    [String]    $Description 
    [System.Collections.Specialized.OrderedDictionary]   $categoryDict
    
    CSVRow ([System.Collections.Specialized.OrderedDictionary] $categoryDict) {
        $this.categoryDict      =     $categoryDict
        $this.Date              =     $this.ValidateDate() 
        $this.Amount            =     $this.ValidateAmount() 
        $this.Description       =     $this.ValidateDescription()
        $this.Category          =     $this.ValidateCategory()
    }

    CSVRow(
        [datetime]$Date, 
        [double]$Amount, 
        [string]$Category, 
        [string]$Description, 
        [System.Collections.Specialized.OrderedDictionary]$categoryDict
        ) {
            $this.categoryDict = $categoryDict
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
        Write-Host "`nParse successfull: '$($tempDate.ToString("dddd, MMMM d, yyyy"))'" -ForegroundColor Green
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
                Write-Host "`nRunning this again, $tempAmount could not be parsed to double" -ForegroundColor Red
            }
        } while ($true)
        Write-Host "`nParse successfull: '$namount'" -ForegroundColor Green
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
        Write-Host "`n Succcessfull parse: '$tempDescription'" -ForegroundColor Green
        return $tempDescription
    }

    hidden [String] ValidateCategory() {
    
        $tempCategory= ""
    
        :CategoryLoop do {
            Write-Host "["
            
            $this.categoryDict.Keys | ForEach-Object { 
                $temporaryValueOfCategoryDict = $this.categoryDict[$_]
                if ($temporaryValueOfCategoryDict -is [string]) {
                    $valueStringToPrint = ": `t$temporaryValueOfCategoryDict,"
                } else {
                    $valueStringToPrint = ","
                }
                Write-Host "`t$_$valueStringToPrint" 
            }
            
            Write-Host "]"
            $key = Read-Host "`nSelect a key from the dictionary above"
            $temp = $this.categoryDict[$key]        
    
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
        return [CSVRow]::new($this.Date, $this.Amount, $this.Category, $this.Description, $this.categoryDict)
    }

}