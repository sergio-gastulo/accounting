using module .\Classes\CSVRow.psm1
using module .\Classes\CSV.psm1
using module .\Classes\GeneralUtilities.psm1

$CSV = [CSV]::new(
    
    # db file (sqlite support)
    # "$PSScriptRoot\files\db-test",
    "$($env:USERPROFILE)\dbs\cuentas",
    
    # json file for categories
    "$PSScriptRoot\files\fields.json",
    
    # plotting script file
    "$PSScriptRoot\acc_py\main.py"
    )

function AccountingCommandLineInterface {
    [alias("acccli")]
    param()

    Write-Host "`nWelcome to 'AccountingCommandLineInterface', please select one of the options below to start using the CLI application.`n" -ForegroundColor Blue

    :mainLoop while ($true) {
        [ordered] @{
            c       =   'clear console'
	        e 	    =   'edit record' 
            h       =   'help'
            p       =   'plot'
            r       =   'read last "n" lines'
            sql     =   'opens "db" in sqlite3'
            w       =   'write'
            wl      =   'write a list'
        } | Format-Table
        Write-Host "Press 'q' to (q)uit."
        $action = Read-Host "Please select which action you would like to perform"

        switch ($action) {
            'r' { 
                Write-Host "`nReading from database." -ForegroundColor Blue
                $CSV.Read()
            }
            'p' {
                Write-Host "`nPlotting from database." -ForegroundColor Blue
                $CSV.Plot()
            }
            'q' {
                Write-Host "`nBreaking Loop. Bye!`n" -ForegroundColor Blue
                break mainLoop
            }
            'w' {
                Write-Host "`nWrite to database." -ForegroundColor Blue
                $CSV.Write([CSVRow]::new($CSV.categoriesJson.hash))
                Write-Host "`n"
            }

            'wl' {
                Write-Host "`nWrite a List to database." -ForegroundColor Blue
                $CSV.WriteList()
            }

            'e' {
                Write-Host "Editing database selected. Currently, no support for data validation. Edit at your own risk."
                $CSV.Edit()
            }

            'c' { Clear-Host }
            'h' { $CSV.Help() }
            'sql' { sqlite3.exe $CSV.DBPATH }

            Default { 
                Clear-Host
                Write-Host "`nNot a valid flag!" -ForegroundColor Red
            }
        }

    }
}
