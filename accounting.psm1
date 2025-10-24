param(
    [string[]] $flags
)


<#
.SYNOPSIS
Installs a specified version of Python on Windows.

.DESCRIPTION
The Install-Python function downloads and installs a specified version of Python
for the current system architecture (x64 or x86).  
If no version is provided, it defaults to 3.13.5.

The function:
- Verifies that it is running in Administrator mode.
- Validates the provided version string format (e.g., 3.12.3).
- Determines system architecture automatically.
- Downloads the official Python installer from python.org.
- Runs the installer silently with system-wide installation and PATH registration.
- Updates the PATH environment variable immediately for the current session.

.PARAMETER Version
(Optional) The specific Python version to install, in semantic version format
(major.minor.patch).  
Example: `3.12.3`

If not provided, defaults to `3.13.5`.

.INPUTS
None.  
This function does not accept pipeline input.

.OUTPUTS
None.  
The function writes progress and error messages to the host.

.EXAMPLE
PS> Install-Python

Installs the default Python version (3.13.5) for the system architecture.

.EXAMPLE
PS> Install-Python -Version 3.12.3

Installs Python 3.12.3 for the current system architecture.

.NOTES
Author: Sergio Gastulo
Date:   2025-10-24
Version: 1.0.0

Requirements:
- Must be run as Administrator.
- Requires internet access to download the installer.
- Works on Windows systems only.

.LINK
https://www.python.org/downloads/
https://learn.microsoft.com/powershell/module/microsoft.powershell.core/about/about_comment_based_help
#>
function Install-Python 
{
    param
    (
        [string] $version
    )

    # check admin
    if (-not (New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
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

    # ensure version and architecture
    $version = if ( -not $version ) { '3.13.5' } else { $version }
    $arch = if ($env:PROCESSOR_ARCHITECTURE -eq 'AMD64') { 'x64' } else { $env:PROCESSOR_ARCHITECTURE.ToLower() }
    $pyInstallationURL = "https://www.python.org/ftp/python/$version/python-$version-$arch.exe" 
    
    # https://stackoverflow.com/questions/46056161/how-to-install-python-using-windows-command-prompt
    Write-Host "Downloading Python $version ($arch) installer..."
    $pyDownloadedFile = Join-Path -Path $env:TEMP -ChildPath "py-installer.exe"
    Invoke-WebRequest -UseBasicParsing $pyInstallationURL -OutFile $pyDownloadedFile
    
    Write-Host "Running silent installation..."
    [System.Diagnostics.Process]::Start
    (
        $pyDownloadedFile, 
        "/quiet InstallAllUsers=1 PrependPath=1 Include_test=0"
    )
        
    $dirVersion = $version.Split(".")[0,1] -join ""
    $pyFolder = "C:\Program Files\Python$dirVersion\"
    [System.Environment]::SetEnvironmentVariable('PATH', $env:PATH + ";$pyFolder", 'Machine') 
    $env:PATH += ";$pyFolder"

    Write-Host "Python $version installed successfully at $pyFolder"
}

<#
.SYNOPSIS
Installs the SQLite3 command-line tools on Windows.

.DESCRIPTION
The Install-SQLite3 function downloads and installs the SQLite3 tools
for the current system architecture (x64 or x86).  

It performs the following actions:
- Verifies that the script is running with Administrator privileges.
- Creates a dedicated installation folder under "C:\Program Files\SQLite3".
- Downloads the official SQLite tools ZIP archive from sqlite.org.
- Extracts the tools into the installation directory.
- Adds the directory to the system-wide PATH environment variable and updates the current session.

.INPUTS
None.  
This function does not accept pipeline input.

.OUTPUTS
None.  
The function writes progress and error messages to the host.

.EXAMPLE
PS> Install-SQLite3

Downloads and installs the latest SQLite3 tools appropriate for the system architecture.

.NOTES
Author: Sergio Gastulo
Date:   2025-10-24
Version: 1.0.0

Requirements:
- Must be run as Administrator.
- Requires internet access to download the installer.
- Works on Windows systems only.

.LINK
https://sqlite.org/download.html
https://learn.microsoft.com/powershell/module/microsoft.powershell.core/about/about_comment_based_help
#>
function Install-SQLite3 
{   
    # check admin
    if (-not (New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        Write-Error `
        -Message "Function is allowed in Administrator Mode only." `
        -Category PermissionDenied
    }

    Write-Host "Installing SQLite3 tools..."

    # create sqlite folder on C:\Program Files
    $sqliteFolder = "SQLite3" 
    $sqliteFolder = New-Item -Path $env:ProgramFiles -Name $sqliteFolderName
    
    # retrieve zip from url
    $arch = if ($env:PROCESSOR_ARCHITECTURE -eq 'AMD64') { 'x64' } else { $env:PROCESSOR_ARCHITECTURE.ToLower() }

    Write-Host "Downloading SQLite3 tools ($arch) from $sqlite3DownloadURL..."
    $sqlite3DownloadURL = "https://sqlite.org/2025/sqlite-tools-win-$arch-3500400.zip"
    $tempSQLZip = Join-Path -Path $env:TEMP -ChildPath "sql.zip"
    Invoke-WebRequest -UseBasicParsing $sqlite3DownloadURL -OutFile $tempSQLZip

    # expand zip on folder
    Write-Host "Extracting SQLite3 tools to $sqliteFolder..."
    Expand-Archive -Path $tempSQLZip -DestinationPath $sqliteFolder

    # append folder to PATH
    [System.Environment]::SetEnvironmentVariable('PATH', $env:PATH + ";$sqliteFolder", 'Machine') 
    $env:PATH += ";$sqliteFolder"

    Write-Host "SQLite3 tools installed successfully at $sqliteFolder"
}


function Test-AccountingHealth 
{
    [alias("test-acc-health")]
    param
    (

    )
    
    try {
        $python = Get-Command python.exe -All
        # this path is just a path to the Microsoft Store. 
        # Should not be a valid python path. 
        $invalidPythonPath = Join-Path -Path $env:LOCALAPPDATA -ChildPath "Microsoft\WindowsApp\python.exe"
        if ( $python[0].Source -eq $invalidPythonPath)
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

    # configuration and paths update
    $configPath = Join-Path -Path $PSScriptRoot -ChildPath ".\config.json"
    $databasePath = (Get-Content $configPath -Raw | ConvertFrom-Json).db_path
    $pythonPath = Join-Path -Path $PSScriptRoot -ChildPath ".\acc_py\main.py"
    $fieldsJSONPath = Join-Path -Path $PSScriptRoot -ChildPath "fields.json"

    switch ($action) 
    {
        'plot'      { python -i $pythonPath $configPath $fieldsJSONPath 'plot' }
        'db'        { python -i $pythonPath $configPath $fieldsJSONPath 'db' }
        'help'      { Get-Help AccountingCommandLineInterface }
        'sql'       { sqlite3.exe $databasePath }
        'backup'
        {
            $date = (get-date).ToString("yyyy-MM-dd")
            $db_name = Join-Path (Split-Path $databasePath) -ChildPath "db-backup-$date.sqlite"
            ".backup $db_name" | sqlite3.exe $databasePath
            Write-Host "Database properly backed up: $db_name" -ForegroundColor Blue
        }
        default { throw "Unknown action: '$action'" }
    }
}

if ( $flags ) 
{
    $flags = $flags.Split(" ")
}
else 
{
    $flags = @()
}

if ( $flags -contains "health" ) 
{
    Write-Host "Flag 'health' detected. Importing Test-AccountingHealth." -ForegroundColor Blue
    Export-ModuleMember -Function Test-AccountingHealth -Alias test-acc-health
}
elseif ( $flags -contains "install" ) 
{
    Write-Host "Flag 'install' detected. Importing Install-Python and Install-SQLite3" -ForegroundColor Blue
    Export-ModuleMember -Function Install-Python,Install-SQLite3
} 
else 
{
    Write-Host "Main function imported: AccountingCommandLineInterface (aka acccli)." -ForegroundColor Blue
    Export-ModuleMember -Function AccountingCommandLineInterface -Alias acccli
}
