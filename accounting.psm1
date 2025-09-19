using module .\Classes\CSVRow.psm1
using module .\Classes\CSV.psm1
using module .\Classes\GeneralUtilities.psm1

$CSV = [CSV]::new(
    
    # db file (sqlite support)
    "$PSScriptRoot\files\db-test",
    # "$($env:USERPROFILE)\dbs\cuentas",
    
    # json file for categories
    "$PSScriptRoot\files\fields.json",
    
    # plotting script file
    "$PSScriptRoot\acc_py\main.py"
    )

function AccountingCommandLineInterface {
    [alias("acccli")]
    param()

    Write-Host "`nWelcome to 'AccountingCommandLineInterface', please select one of the options below to start using the CLI application.`n" -ForegroundColor Blue
    Write-Host "'db' selected: $($CSV.DBPATH)"
    :mainLoop while ($true) {
        [ordered] @{
            b       =   "backup $($CSV.DBPATH)"
            cls     =   "clear console"
            db      =   "DB management CLI: opens a python session with pre-loaded functions for db management"
            h       =   "help"
            p       =   "Plot CLI: opens a python session with pre-loaded functions for plotting"
            sql     =   "opens 'db' in sqlite3"
        } | Format-Table
        Write-Host "Press 'q' to (q)uit."
        $action = Read-Host "Please select which action you would like to perform"

        switch ($action) {
            'r' { # python
                Write-Host "`nReading from database." -ForegroundColor Blue
                $CSV.Read()
            }
            'p' { # python
                Write-Host "`nRuning python for plotting." -ForegroundColor Blue
                python -i $CSV.PYTHONSCRIPTPATH $CSV.DBPATH $CSV.JSONPATH 'plot'
            }
            'q' {
                Write-Host "`nBreaking Loop. Bye!`n" -ForegroundColor Blue
                break mainLoop
            }
            'w' { # python
                Write-Host "`nWrite to database." -ForegroundColor Blue
                $CSV.Write([CSVRow]::new($CSV.categoriesJson.hash))
                Write-Host "`n"
            }

            'wl' { # python
                Write-Host "`nWrite List of records to database." -ForegroundColor Blue
                $CSV.WriteList()
            }

            'e' { # python
                Write-Host "Editing database selected. Currently, no support for data validation. Edit at your own risk." -ForegroundColor Yellow
                $CSV.Edit()
            }

            'b' { # leave pwsh
                $date = (get-date).ToString("yyyy-MM-dd")
                $db_name = Join-Path (Split-Path $CSV.DBPATH) -ChildPath "db-backup-$date.sqlite"
                ".backup $db_name" | sqlite3.exe $CSV.DBPATH 
            }
            'db'{
                python -i $CSV.PYTHONSCRIPTPATH $CSV.DBPATH $CSV.JSONPATH 'db'
            }
            'cls' { Clear-Host }
            'h' { $CSV.Help() } # python
            'sql' { sqlite3.exe $CSV.DBPATH }

            Default {
                Clear-Host
                Write-Host "`nNot a valid flag!" -ForegroundColor Red
            }
        }

    }
}
