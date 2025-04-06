class CSV {
    static [String]$CSVPATH = 'C:\Users\sgast\PROJECTS\Modules\accounting\cuentas.csv'

    static [int] ValidateInstallments() {
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
    
    static [Void] Read(){
        
        $numberOfLines = Read-Host "`nInsert number of lines to be read"
        Get-Content -Path ([CSV]::CSVPATH) -Tail $numberOfLines | Write-Host

    }

    static [Void] Write([CSVRow]$data){

        if (($data.Amount -gt 200) -and -not ($data.Category -in @("BLIND","INGRESO-SOLES","INGRESO-USD"))) {

            $installments = [CSV]::ValidateInstallments()
            $data.Amount = $data.Amount / $installments

            for ($i = 0; $i -lt $installments; $i++) {
                $tempData = $data.Copy()

                $tempdata.Date = $data.Date.AddMonths($i)                
                $tempData.Description = "$($data.Description) tag: cuota $i"
                Add-Content -Path ([CSV]::CSVPATH) -Value ($tempData.Parse())
            }
        } else {
            Add-Content -Path ([CSV]::CSVPATH) -Value ($data.Parse())
        }
        Write-Host "`nData added." -ForegroundColor Blue
    }

    static [void] Plot(){
        Write-Host "Plotting data."
    }
}