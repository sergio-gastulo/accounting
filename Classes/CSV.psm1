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
        Clear-Host
        [GeneralUtilities]::GetSQLQuery(
            "read.sql", 
            @{
                today           = (Get-Date).ToString("yyyy-MM-dd")
                numberOfLines   = [GeneralUtilities]::ValidateInteger("Lines to read", 0)
            }) | sqlite3.exe -header -column -header -column ($this.DBPATH) | Write-Host -Separator "`n"
            Read-Host "Press any key to continue"
    }

    [Void] Write([CSVRow]$data){

        # lambda function for writing
        $write = {
            param($csvParsed)
            [GeneralUtilities]::GetSQLQuery(
                "write.sql",
                $csvParsed 
            ) | sqlite3.exe ($this.DBPATH)
        }

        if (($data.Amount -gt 200) -and -not ($data.Category -in @("BLIND","INGRESO"))) {

            $installments = [GeneralUtilities]::ValidateInteger("Installments", 1)
            $data.Amount = $data.Amount / $installments

            for ($i = 0; $i -lt $installments; $i++) {
                $tempData = $data.Copy()

                $tempdata.Date = $data.Date.AddMonths($i)
                $tempData.Description = "$($data.Description) tag: cuota $i"

                $write.Invoke($tempData.Parse())
            }

        } else {
            $write.Invoke($data.Parse())
        }
            Write-Host "`nThe following line has been written to file:" -ForegroundColor Green
            $data.Parse() | ConvertTo-Json -Depth 4 | Write-Host -Separator "`n" -ForegroundColor Blue
		}


    [void] Plot(){
        # as per https://github.com/python/cpython/issues/132962
        $env:PYTHON_BASIC_REPL = "anyvalue"; python -i $this.PYTHONSCRIPTPATH $this.DBPATH $this.JSONPATH | Write-Host -Separator "`n"
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

    [void] Edit() {
        $recordID = 0
        do {
            $recordID = Read-Host "Write the ID you would like to edit, press 'r' to read"
            if ($recordID -eq 'r') {
                $this.Read()
                $recordID = $null
            }
        } until ($recordID -match "^\d+$")
        $recordID = [int]$recordID

        Write-Host "Available columns:" -ForegroundColor Blue
        # manually writing columns from schema
        "SELECT name, type FROM pragma_table_info('cuentas')" | sqlite3.exe -header -column $this.DBPATH | Write-Host -Separator "`n"
        $column = Read-Host "Write the column you would like to modify"
        $value = Read-Host "Write the attribute you would like to edit"

        # if column is a numeric value (due to the schema, if column=amount), do not add '' (otherwise, it could be recognized as string)
        if (-not ($column -eq 'amount')) {
            $value = "'$value'"
        }
        
        [GeneralUtilities]::GetSQLQuery("edit.sql", @{
            id=$recordID
            column=$column
            value=$value
        }) | sqlite3.exe $this.DBPATH

    }

    [void] WriteList(){
        $opt = ""
        $date = [GeneralUtilities]::ValidateDate()
        $category = [GeneralUtilities]::ValidateCategory($this.categoriesJson.hash)
        $currency = [GeneralUtilities]::ValidateCurrency("not-a-valid-currency")
        while($true){
            $this.Write([CSVRow]::new($date, $category, $currency))
            do {
                $opt = Read-Host "Would you like to continue? (y/n)"
            } until ($opt -match '^[yn]$')
            if ($opt -eq 'n') { return }
        }
    }
}
