using module .\GeneralUtilities.psm1

class CSVRow {
    [datetime]  $Date
    [double]    $Amount
    [string]    $Description 
    [string]    $Category
    [string]    $Currency
    [System.Collections.Specialized.OrderedDictionary]   $categoryDict
    
    CSVRow ([System.Collections.Specialized.OrderedDictionary] $categoryDict) {
        $this.categoryDict      =       $categoryDict
        $this.Date              =       [GeneralUtilities]::ValidateDate() 
        # temp variable
        $amountCurrency         =       [GeneralUtilities]::ValidateDoubleCurrency("Amount", 0.0)
        $this.Amount            =       $amountCurrency[0]
        $this.Currency          =       $amountCurrency[1]
        $this.Description       =       [GeneralUtilities]::ValidateStringForCSV("Description")
        $this.Category          =       $this.ValidateCategory()
    }

    CSVRow(
        [datetime]$Date, 
        [double]$Amount, 
        [string]$Category, 
        [string]$Description, 
        [string]$Currency,
        [System.Collections.Specialized.OrderedDictionary]$categoryDict
        ) {
            $this.categoryDict = $categoryDict
            $this.Date = $Date
            $this.Amount = $Amount
            $this.Category = $Category
            $this.Description = $Description
            $this.Currency = $Currency
    }
    
    # Only god knows what I did here 
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

    [hashtable]Parse(){

        return @{
            date        = $this.Date.ToString("yyyy-MM-dd")
            amount      = $this.Amount
            description = $this.Description
            category    = $this.Category
            currency    = $this.Currency
        }

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
        return [CSVRow]::new($this.Date, $this.Amount, $this.Category, $this.Description, $this.Currency, $this.categoryDict)
    }

}