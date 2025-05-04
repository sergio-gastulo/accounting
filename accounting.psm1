using module .\Classes\CSVRow.psm1
using module .\Classes\CSV.psm1

$CSV = [CSV]::new(
    # csv file
    "$PSScriptRoot\files\cuentas.csv",
    # json file
    "$PSScriptRoot\files\fields.json",
    # python script file
    "$PSScriptRoot\plot.py"
    )

function AccountingCommandLineInterface {
    [alias("acccli")]
    param()

    Write-Host "`nWelcome to 'AccountingCommandLineInterface', please select one of the options below to start using the CLI application.`n" -ForegroundColor Blue

    :mainLoop while ($true) {

        @{
            p   =   'plot'
            q   =   'quit'
            r   =   'read'
            w   =   'write'
        } | ConvertTo-Json -Depth 4

        $action = Read-Host "`nPlease select which action you would like to perform" -ForegroundColor Blue

        switch ($action) {
            'r' { 
                Write-Host "`nRead Data selected." -ForegroundColor Blue
                $CSV.Read()
            }

            'w' { 
                Write-Host "`nWrite Data selected." -ForegroundColor Blue
                $data = [CSVRow]::new($CSV.GetJSON())
                $CSV.Write($data)
            }

            'p' {
                Write-Host "`nPlotting data." -ForegroundColor Blue
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