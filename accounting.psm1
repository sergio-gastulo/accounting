using module .\Classes\CSVRow.psm1
using module .\Classes\CSV.psm1

$CSV = [CSV]::new(
    
    # db file (sqlite support)
    "$($env:USERPROFILE)\dbs\cuentas",
    
    # json file for categories
    "$PSScriptRoot\files\fields.json",
    
    # plotting script file
    "$PSScriptRoot\Python\plot.py"
    )

function AccountingCommandLineInterface {
    [alias("acccli")]
    param()

    Write-Host "`nWelcome to 'AccountingCommandLineInterface', please select one of the options below to start using the CLI application.`n" -ForegroundColor Blue

    :mainLoop while ($true) {

        [ordered] @{
            c       =   'clear console'
            # We are disabling this option, will need to edit it carefuly -- will have to test how to edit 'user-friendlyly'.
	        # e 	=   'edit on vim' 
            h       =   'help'
            # We are disabling this option too, no need to do interactive filtering if one can now open the sqlite3 CLI.
            # i   =   'interactive playground' 
            p       =   'plot' # missing this
            r       =   'read'
            sql     =   'opens "db" in sqlite3'
            w       =   'write'
        } | ConvertTo-Json -Depth 4
        Write-Host "Press 'q' to (q)uit."

        $action = Read-Host "`nPlease select which action you would like to perform"

        switch ($action) {
            'r' { 
                Write-Host "`nRead Data selected." -ForegroundColor Blue
                $CSV.Read()
            }

            'w' {
                Write-Host "`nWrite Data selected." -ForegroundColor Blue
                $data = [CSVRow]::new($CSV.categoriesJson.hash)
                $CSV.Write($data)
                Write-Host "`n"
            }

            'p' {
                Write-Host "`nPlotting data." -ForegroundColor Blue
                $CSV.Plot()
            }

            'q' {
                Write-Host "`nBreaking Loop. Bye!`n" -ForegroundColor Blue
                break mainLoop
            }

            'c' { Clear-Host }

            'h' { $CSV.Help() }

            'sql' { sqlite3.exe $CSV.DBPATH }

            Default { Write-Host "`nNon-valid flag!" -ForegroundColor Red }
        }

    }
}
