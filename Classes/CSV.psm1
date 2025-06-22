using module .\CSVRow.psm1
using module .\GeneralUtilities.psm1

class CSV {
    [string]    $CSVPATH
    [string]    $JSONPATH
    [string]    $PYTHONSCRIPTPATH
    [string]    $IPYTHONPATH
    [object]    $categoriesJson


    CSV([string] $csvpath, [string] $jsonpath, [string] $pythonpath, [string] $iPythonPath) {
        $this.CSVPATH = $csvpath
        $this.JSONPATH = $jsonpath
        $this.PYTHONSCRIPTPATH = $pythonpath
        $this.IPYTHONPATH = $iPythonPath
        $this.categoriesJson = [GeneralUtilities]::GetJSON($jsonpath)
    }


    [Void] Read(){
        
        $numberOfLines = [GeneralUtilities]::ValidateInteger("Lines to read", 1)
        Write-Host "`n"
        Get-Content -Path ($this.CSVPATH) -Tail $numberOfLines | Write-Host
        Write-Host "`n"

    }

    [Void] Write([CSVRow]$data){

        if (($data.Amount -gt 200) -and -not ($data.Category -in @("BLIND","INGRESO-SOLES","INGRESO-USD"))) {

            $installments = [GeneralUtilities]::ValidateInteger("Installments", 1)
            $data.Amount = $data.Amount / $installments

            for ($i = 0; $i -lt $installments; $i++) {
                $tempData = $data.Copy()

                $tempdata.Date = $data.Date.AddMonths($i)
                $tempData.Description = "$($data.Description) tag: cuota $i"
                Add-Content -Path ($this.CSVPATH) -Value ($tempData.Parse())
                if ($i -eq $installments - 1) {
                    Write-Host "`nSeveral lines have been written to file. Sample: $($tempData.Parse())"
                }
            }

        } else {
            Add-Content -Path ($this.CSVPATH) -Value ($data.Parse())
        }
        Write-Host "`nThe following line has been written to file: `n$($data.Parse())" -ForegroundColor Blue
        Write-Host "`nData added." -ForegroundColor Green
    }

    [void] Plot(){
        python $this.PYTHONSCRIPTPATH $this.CSVPATH $this.JSONPATH | ForEach-Object {
            Write-Host $_
        }
    }

}