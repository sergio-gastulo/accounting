using module .\Classes\CSVRow.psm1
using module .\Classes\CSV.psm1

$CSV = [CSV]::new("$PSScriptRoot\files\cuentas.csv","$PSScriptRoot\files\fields.json")

function AccountingCommandLineInterface {
    [alias("acccli")]
    param()

    :mainLoop while ($true) {

        @{
            p   =   'plot'
            q   =   'quit'
            r   =   'read'
            w   =   'write'
        } | ConvertTo-Json -Depth 4

        $action = Read-Host "Please select which action you would like to perform"

        switch ($action) {
            'r' { 
                Write-Host "`nRead Data selected."
                $CSV.Read()
            }

            'w' { 
                Write-Host "`nWrite Data selected."
                $data = [CSVRow]::new($CSV.JSONDICT)
                $CSV.Write($data)
            }

            'p' {
                Write-Host "`nPlotting data."
                $CSV.Plot()
            }

            'q' {
                Write-Host "`nBreaking Loop. Bye!`n" -ForegroundColor Blue
                break mainLoop
            }

            Default {
                Write-Host "Non-valid flag" -ForegroundColor Red
            }
        }

    }
}