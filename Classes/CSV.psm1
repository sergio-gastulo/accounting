using module .\CSVRow.psm1
using module .\GeneralUtilities.psm1

class CSV {
    [string]    $DBPATH
    [string]    $JSONPATH
    [string]    $PYTHONSCRIPTPATH
    [object]    $categoriesJson


    CSV([string] $dbpath, [string] $jsonpath, [string] $pythonpath) {
        $this.DBPATH = $dbpath
        $this.JSONPATH = $jsonpath
        $this.PYTHONSCRIPTPATH = $pythonpath
        $this.categoriesJson = [GeneralUtilities]::GetJSON($jsonpath)
    }


    [Void] Read(){
        [GeneralUtilities]::GetSQLQuery(
            "read.sql", 
            @{
                today           = (Get-Date).ToString("yyyy-MM-dd")
                numberOfLines   = [GeneralUtilities]::ValidateInteger("Lines to read", 0) 
            }) | sqlite3.exe ($this.DBPATH) | Write-Host -Separator "`n"
    }

    [Void] Write([CSVRow]$data){

        # lambda function for writing
        $write = {
            param($csvParsed, $db)
            [GeneralUtilities]::GetSQLQuery(
                "write.sql",
                $csvParsed 
            ) | sqlite3.exe ($db)
        }

        if (($data.Amount -gt 200) -and -not ($data.Category -in @("BLIND","INGRESO"))) {

            $installments = [GeneralUtilities]::ValidateInteger("Installments", 1)
            $data.Amount = $data.Amount / $installments

            for ($i = 0; $i -lt $installments; $i++) {
                $tempData = $data.Copy()

                $tempdata.Date = $data.Date.AddMonths($i)
                $tempData.Description = "$($data.Description) tag: cuota $i"

                $write.Invoke($tempData.Parse(), $this.DBPATH)
            }

        } else {
            $write.Invoke($data.Parse(), $this.DBPATH)
        }
        Write-Host "`nThe following line has been written to file: `n$($data.Parse() | ConvertTo-Json -Compress)" -ForegroundColor Blue
        Write-Host "`nData added." -ForegroundColor Green
    }

    [void] Plot(){
        python $this.PYTHONSCRIPTPATH $this.DBPATH $this.JSONPATH | ForEach-Object {
            Write-Host $_
        }
    }

    [void] Help(){

        $strTemplate = "{0}: {1}"
        $this.categoriesJson.array | ForEach-Object {
            
            $strTemplate -f $_.shortname, $_.description | Write-Host
            $indent  = " " * ($_.shortname.Length + 2)
            if ($_.help) {
                $indent + $_.help | Write-Host
            }
            
            if ($_.subcategories) {
                Write-Host "$indent The following subcategories are:"
                $indent  += " " * ($_.shortname.Length + 3)
                $_.subcategories | ForEach-Object {
                    $indent + ($strTemplate -f $_.shortname, $_.description) | Write-Host
                    if ($_.help) {
                        $indent + $_.help | Write-Host
                    }
                }
            }
        }
    }
}