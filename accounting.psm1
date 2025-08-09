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
                $date = [GeneralUtilities]::ValidateDate()
                $category = [GeneralUtilities]::ValidateCategory($CSV.categoriesJson.hash)
                $currency = [GeneralUtilities]::ValidateCurrency("")
                :listLoop while($true){
                    $CSV.Write([CSVRow]::new($date, $category, $currency))
                    do {
                        $opt = Read-Host "Would you like to continue? (y/n)"
                    } until ($opt -match '^[yn]$')
                    if ($opt -eq 'n') { break listLoop}
                }
            }

            'c' { Clear-Host }

            'h' { $CSV.Help() }

            'sql' { sqlite3.exe $CSV.DBPATH }

            Default { Write-Host "`nNon-valid flag!" -ForegroundColor Red }
        }

    }
}
