
$DBPATH             =   "$($env:USERPROFILE)\dbs\cuentas"
$JSONPATH           =   "$PSScriptRoot\files\fields.json"
$PYTHONSCRIPTPATH   =   "$PSScriptRoot\acc_py\main.py"

function Install-Python 
{
    param
    (
        [string] $version
    )

    # check admin
    if ((New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        Write-Error `
        -Message "Function is allowed in Administrator Mode only." `
        -Category PermissionDenied
    }

    # check version regex
    if ( $version -and $version -notmatch  "^\d\.\d{1,2}\.\d$" ) 
    {
        Write-Error `
        -Message "Not a valid version format has been specified: '$version'." `
        -Category InvalidArgument
    }

    # ensure version
    $version = if ( -not $version ) { '3.13.5' } else { $version }
    $arch = if ($env:PROCESSOR_ARCHITECTURE -eq 'AMD64') { 'x64' } else { $env:PROCESSOR_ARCHITECTURE.ToLower() }
    $pyInstallationURL = "https://www.python.org/ftp/python/$version/python-$version-$arch.exe" 
    
    # download python
    # https://stackoverflow.com/questions/46056161/how-to-install-python-using-windows-command-prompt
    $pyDownloadedFile = Join-Path -Path $env:TEMP -ChildPath "py-installer.exe"
    Invoke-WebRequest -UseBasicParsing $pyInstallationURL -OutFile $pyDownloadedFile
    [System.Diagnostics.Process]::Start
    (
        $pyDownloadedFile, 
        "/quiet InstallAllUsers=1 PrependPath=1 Include_test=0"
    )
        
    $dirVersion = $version.Split(".")[0,1] -join ""
    $pyFolder = "C:\Program Files\Python$dirVersion\"
    [System.Environment]::SetEnvironmentVariable('PATH', $env:PATH + ";$pyFolder", 'Machine') 
    $env:PATH += ";$pyFolder"

}


function Install-SQLite3 
{   
    # check admin
    if ((New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        Write-Error `
        -Message "Function is allowed in Administrator Mode only." `
        -Category PermissionDenied
    }

    # create sqlite folder on C:\Program Files
    $sqliteFolder = "SQLite3" 
    $sqliteFolder = New-Item -Path $env:ProgramFiles -Name $sqliteFolderName
    
    # retrieve zip from url
    $arch = if ($env:PROCESSOR_ARCHITECTURE -eq 'AMD64') { 'x64' } else { $env:PROCESSOR_ARCHITECTURE.ToLower() }

    $sqlite3DownloadURL = "https://sqlite.org/2025/sqlite-tools-win-$arch-3500400.zip"
    $tempSQLZip = Join-Path -Path $env:TEMP -ChildPath "sql.zip"
    Invoke-WebRequest -UseBasicParsing $sqlite3DownloadURL -OutFile $tempSQLZip

    # expand zip on folder
    Expand-Archive -Path $tempSQLZip -DestinationPath $sqliteFolder

    # append folder to PATH
    [System.Environment]::SetEnvironmentVariable('PATH', $env:PATH + ";$sqliteFolder", 'Machine') 
    $env:PATH += ";$sqliteFolder"
}


function Test-AccountingHealth 
{
    [alias("acc-health")]
    param
    (

    )
    
    # check python
    $res = where.exe python > $null 2>&1
    try { 
        # if res arises an error, then python is non-existent
        $res

        # this path is just a path to the Microsoft Store. 
        # Should not be a valid python path. 
        if ( $res[0] -eq "C:\Users\sgast\AppData\Local\Microsoft\WindowsApps\python.exe" )
        {
            throw
        }
        else 
        {
            Write-Host "Python is succesfully installed on this machine:" -ForegroundColor Blue
            python.exe --version
        }
    } 
    catch 
    {
        Write-Warning "python.exe is not installed on this computer."
        Write-Host "If you would like to install python, please execute Install-Python from Powershell with elevated privileges."
        Write-Host "To launch powershell with elevated privileges, you can execute 'saps powershell -verb runas' and import the module again."
    }

    # check sqlite3
    where.exe sqlite3 > $null 2>&1
    if ( $LASTEXITCODE -eq 1 )
    {
        Write-Warning "sqlite3.exe is not installed on this computer."
        Write-Host "If you would like to install sqlite3, please execute 'Install-SQLite3' from Powershell with elevated privileges."
        Write-Host "To launch powershell with elevated privileges, you can execute 'saps powershell -verb runas' and import the module again."
    }
    else
    {
        Write-Host "Sqlite3 is succesfully installed on this machine:" -ForegroundColor Blue
        sqlite3.exe --version
    }
}



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
        default { throw "Unknown action: '$action'" }
    }
}