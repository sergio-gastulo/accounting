using module .\GeneralUtilities.psm1

class CSVRow {
    [datetime]  $Date
    [double]    $Amount
    [string]    $Currency
    [string]    $Description 
    [string]    $Category
    
    CSVRow ([System.Collections.Specialized.OrderedDictionary] $categoryDict) {
        $this.Date              =       [GeneralUtilities]::ValidateDate() 
        $amountCurrency         =       [GeneralUtilities]::ValidateDoubleCurrency("Amount")
        $this.Amount            =       $amountCurrency[0]
        $this.Currency          =       $amountCurrency[1]
        $this.Description       =       [GeneralUtilities]::ValidateStringForCSV("Description")
        $this.Category          =       [GeneralUtilities]::ValidateCategory($categoryDict)
    }

    CSVRow(
        [datetime]  $Date, 
        [double]    $Amount, 
        [string]    $Category, 
        [string]    $Description, 
        [string]    $Currency
        ) {
            $this.Date = $Date
            $this.Amount = $Amount
            $this.Category = $Category
            $this.Description = $Description
            $this.Currency = $Currency
    }

    #for Writing a list to database support
    CSVRow(
        [datetime] $date,
        [string] $category
    ){
        $this.Date              =       $date 
        $this.Category          =       $category
        # temp variable
        $amountCurrency         =       [GeneralUtilities]::ValidateDoubleCurrency("Amount")
        $this.Amount            =       $amountCurrency[0]
        $this.Currency          =       $amountCurrency[1]
        $this.Description       =       [GeneralUtilities]::ValidateStringForCSV("Description")
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
        return [CSVRow]::new($this.Date, $this.Amount, $this.Category, $this.Description, $this.Currency)
    }

}