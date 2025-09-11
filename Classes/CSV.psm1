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
		$parse = ""
        if (($data.Amount -gt 200) -and -not ($data.Category -in @("BLIND","INGRESO"))) {

            $installments = [GeneralUtilities]::ValidateInteger("Installments", 1)
            $data.Amount = $data.Amount / $installments

            for ($i = 0; $i -lt $installments; $i++) {
                $tempData = $data.Copy()

                $tempdata.Date = $data.Date.AddMonths($i)
                $tempData.Description = "$($data.Description) tag: cuota $i"
				$parse = $tempData.Parse()	
                $write.Invoke($parse)
            }

        } else {
			$parse = $data.Parse()	
            $write.Invoke($parse)
        }
            Write-Host "`nThe following line has been written to file:" -ForegroundColor Green
            $parse | ConvertTo-Json -Depth 4 | Write-Host -Separator "`n" -ForegroundColor Blue
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
        $date = ([GeneralUtilities]::ValidateDate()).ToString("yyyy-MM-dd")
        $category = [GeneralUtilities]::ValidateCategory($this.categoriesJson.hash)
        $currency = [GeneralUtilities]::ValidateCurrency("not-a-valid-currency")
        $file = Join-Path -Path $env:TEMP -ChildPath "temp-acccli.txt"
        New-Item $file -Force
        Set-Content $file "date,description"
        Write-Host "Openning editor..." -ForegroundColor Blue
        Start-Process notepad++.exe -ArgumentList $file -Wait
        $content = (Get-Content $file).Split("`n")

		$tasa = if ($Global:tasa) { $Global:tasa } else { 1 }
		Write-Host "Current multiplier: '$tasa'" -ForegroundColor Blue

        $values = foreach ($i in 1..($content.Count - 1)){
            $amount, $description = $content[$i].Split(",")
			$amount *= $tasa
            "('$date', '$currency', $amount, '$description', '$category')"
        }
        $values = $values -join ",`n"
        $sqlString = "INSERT INTO cuentas (date, currency, amount, description, category) VALUES $values;"
        $sqlString | sqlite3.exe $this.DBPATH
        Write-Host "Query executed." -ForegroundColor Green

        }
}
