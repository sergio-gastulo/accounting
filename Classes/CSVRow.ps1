class CSVRow {
    [datetime]  $Date
    [Double]    $Amount
    [String]    $Category
    [String]    $Description 
    
    CSVRow () {
        $this.Date = (Get-Date)
        $this.Amount = 0
        $this.Category = "BLIND"
        $this.Description = "test"
    }

    hidden [datetime] ValidateDate() {
        $tempDate = (Get-Date)
        
        while($true){
            $day = Read-Host "`nInsert a day"
            $month = Read-Host "`nInsert a month"
            try {
                $tempDate = Get-Date -Day $day -Month $month
                break
            }
            catch {
                $flag = Read-Host "Running this again, could not parse $day and $month.`nIf you wish to leave and choose today as date, press 'x'. Otherwise, press any button"
                if($flag -eq 'x'){
                    break
                }
            }
        }
        return $tempDate
    }

    hidden [double] ValidateAmount() {
        return 0.0
    }

    hidden [String] ValidateDescription() {
        return "test"
    }

    hidden [String] ValidateCategory() {
        return "JSON"
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
Category:    $($this.Category)
Description: $($this.Description)
"@
    }

}

$data = [CSVRow]::new()

Write-Host $data




