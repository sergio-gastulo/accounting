class Data {
    [datetime]$Date
    [Double]$Amount
    [String]$Category
    [String]$Description

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
Category:    $($this.Category)
Description: $($this.Description)
"@
    }

}

class CSV {
    static [String]$CSVPATH = "C:\Users\sgast\PROJECTS\Modules\accounting\cuentas.csv"

    static [Void] Read(){
        
        $numberOfLines = Read-Host "`nInsert number of lines to be read"
        Get-Content -Path ([CSV]::CSVPATH) -Tail $numberOfLines | Write-Host

    }

    static [Void] Write([Data]$data){
        if (($data.Amount -gt 200) -and -not ($data.Category -in @("BLIND","INGRESO","USD_INC"))) {

            $installments = Read-Host "`nSelect number of installments"
            $data.Amount = $data.Amount / [int]$installments

            for ($i = 0; $i -lt $installments; $i++) {
                $tempData = New-Object Data
                $tempData.Category = $data.Category
                $tempData.Amount = $data.Amount
                $tempdata.Date = $data.Date.AddMonths($i)
                
                $tempData.Description = "$($data.Description) tag: cuota $i"
                Add-Content -Path ([CSV]::CSVPATH) -Value ($tempData.Parse())
            }
        } else {
            Add-Content -Path ([CSV]::CSVPATH) -Value ($data.Parse())
        }
        Write-Host "Data added."
    }

    static [void] Plot(){
        Write-Host "Plotting data."
    }
}


#Data sample

# $data = New-Object Data
# $data.Amount = 500.00
# $data.Category = "PERSONAL"
# $data.Description = "test"
# $data.Date = Get-Date

[CSV]::Read()