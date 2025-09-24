
$DBPATH             =   "$($env:USERPROFILE)\dbs\cuentas"
$JSONPATH           =   "$PSScriptRoot\files\fields.json"
$PYTHONSCRIPTPATH   =   "$PSScriptRoot\acc_py\main.py"


<#
.SYNOPSIS
    CLI wrapper for main python scripts.

.DESCRIPTION
    The AccountingCommandLineInterface (alias: acccli) function provides a PowerShell
    interface for plotting data, interacting with the database, running SQL commands, 
    backing up the database, and showing help information.
    
    It wraps underlying Python scripts and SQLite operations for ease of use.

.PARAMETER action
    Specifies the action to perform. Valid actions are:

    - 'plot'   : Plot accounting data.
    - 'db'     : Perform database-related operations: write, edit, delete, etc.
    - 'help'   : Displays this message.
    - 'sql'    : Opens SQLite for manual SQL queries.
    - 'backup' : Creates a timestamped backup of the SQLite database in the same directory.

.NOTES
    - Depends on Python and sqlite3.exe being available in the system PATH.
    - The function is aliasable with 'acccli' for convenience.

#>

function AccountingCommandLineInterface 
{
    [alias("acccli")]
    param
    (
        [Parameter(Mandatory=$true)]
        [ValidateSet("backup", "db", "help", "plot", "sql")]
        [string]$action
    )

    while ($true) 
    {
        switch ($action) 
        {
            'plot'      { python -i $PYTHONSCRIPTPATH $DBPATH $JSONPATH 'plot' }
            'db'        { python -i $PYTHONSCRIPTPATH $DBPATH $JSONPATH 'db' }
            'help'      { Get-Help AccountingCommandLineInterface }
            'sql'       { sqlite3.exe $DBPATH }
            'backup' 
            {
                $date = (get-date).ToString("yyyy-MM-dd")
                $db_name = Join-Path (Split-Path $DBPATH) -ChildPath "db-backup-$date.sqlite"
                ".backup $db_name" | sqlite3.exe $DBPATH
                Write-Host "Database properly backed up: $db_name" -ForegroundColor Blue
            }
            default { throw "Unknown action: $action" }
        }
        
    }

}