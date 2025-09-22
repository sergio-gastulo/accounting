
$DBPATH             =   "$($env:USERPROFILE)\dbs\cuentas"
$JSONPATH           =   "$PSScriptRoot\files\fields.json"
$PYTHONSCRIPTPATH   =   "$PSScriptRoot\acc_py\main.py"

function AccountingCommandLineInterface {
    [alias("acccli")]
    param()

    Write-Host "`nWelcome to 'AccountingCommandLineInterface', please select one of the options below to start using the CLI application.`n" -ForegroundColor Blue
    Write-Host "'db' selected: $($DBPATH)"
    :mainLoop while ($true) {
        [ordered] @{
            b       =   "backup $($DBPATH)"
            cls     =   "clear console"
            db      =   "DB management CLI: opens a python session with pre-loaded functions for db management"
            h       =   "help"
            p       =   "Plot CLI: opens a python session with pre-loaded functions for plotting"
            sql     =   "opens 'db' in sqlite3"
        } | Format-Table
        Write-Host "Press 'q' to (q)uit."
        $action = Read-Host "Please select which action you would like to perform"

        switch ($action) {
            'p' {
                python -i $PYTHONSCRIPTPATH $DBPATH $JSONPATH 'plot'
            }
            'q' {
                Write-Host "`nBreaking Loop. Bye!`n" -ForegroundColor Blue
                break mainLoop
            }
            'b' {
                $date = (get-date).ToString("yyyy-MM-dd")
                $db_name = Join-Path (Split-Path $DBPATH) -ChildPath "db-backup-$date.sqlite"
                ".backup $db_name" | sqlite3.exe $DBPATH 
            }
            'db'{
                python -i $PYTHONSCRIPTPATH $DBPATH $JSONPATH 'db'
            }
            'cls'   { Clear-Host }
            'h'     { $CSV.Help() } # python
            'sql'   { sqlite3.exe $DBPATH }

            Default {
                Clear-Host
                Write-Host "`nNot a valid flag!" -ForegroundColor Red
            }
        }

    }
}
