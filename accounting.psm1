using module .\Classes\CSVRow.psm1
using module .\Classes\CSV.psm1

$CSV = [CSV]::new(
    # csv file
    "$PSScriptRoot\files\cuentas.csv",
    # json file
    "$PSScriptRoot\files\fields.json",
    # plotting script file
    "$PSScriptRoot\Python\plot.py",
    # interactive script file
    "$PSScriptRoot\Python\console.py"
    )

function AccountingCommandLineInterface {
    [alias("acccli")]
    param()

    Write-Host "`nWelcome to 'AccountingCommandLineInterface', please select one of the options below to start using the CLI application.`n" -ForegroundColor Blue

    :mainLoop while ($true) {

        [ordered] @{
            c   =   'clear console'
	    e 	=   'edit on vim'
            f   =   'filter'
            h   =   'help'
            i   =   'interactive playground'
            p   =   'plot'
            q   =   'quit'
            r   =   'read'
            w   =   'write'
        } | ConvertTo-Json -Depth 4

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
            }

            'p' {
                Write-Host "`nPlotting data." -ForegroundColor Blue
                $CSV.Plot()
            }

            'q' {
                Write-Host "`nBreaking Loop. Bye!`n" -ForegroundColor Blue
                break mainLoop
            }

            'c' {
                Clear-Host
            }

            'h' {
                $strTemplate = "{0}: {1}"
                $CSV.categoriesJson.array | ForEach-Object {
                    
                    $strTemplate -f $_.shortname, $_.description | Write-Host
                    $indent  = " " * ($_.shortname.Length + 2)
                    if ($_.help) {
                        $indent + $_.help | Write-Host
                    }
                    
                    if ($_.subcategories) {
                        Write-Host "$indent The following subcategories are:"
                        $indent  += " " * ($_.shortname.Length + 3)
                        $_.subcategories | ForEach-Object {
                            $indent + ($strTemplate -f $_.shortname, $_.description) | Write-Host
                            if ($_.help) {
                                $indent + $_.help | Write-Host
                            }
                        }
                    }
                }
            }

            'f' {
                $bodyOfCSV = Get-Content $CSV.CSVPATH
                
                :subFilterLoop do {
                    
                    $pattern = Read-Host "`nEnter the filter string (regex)"
                    $search = $bodyOfCSV | Select-String -Pattern $pattern
                    if ($search) {
                        $search | Write-Host
                    } else {
                        Write-Host "`nNo match for $pattern!" -ForegroundColor Red
                    }
                    Write-Host "`nWould you like to exit the loop? (y/n)" -ForegroundColor Blue
                    $option = Read-Host
                    if ($option -eq 'y') {
                        break subFilterLoop 
                    } else {
                        Write-Host "`nKeep filtering!"
                    }
                } while ($true)

            }

	    'e' {
		Write-Host "`nSelect (v)im or (n)otepad++."
		Write-Host "`nIf none is available, notepad will be chosen."
		$option = Read-Host
		switch ($option) {
			'v' {
				vim $CSV.CSVPATH
			} 
			'n' {
				notepad++.exe $CSV.CSVPATH
			}
			Default {
				Write-Host "`nRunning default notepad for Windows."
				Start-Process notepad -ArgumentList $CSV.CSVPATH
			}				
		}			
			$CSV.CSVPATH	    
	    }	

            'i' {
                $option = Read-Host "`nSelect whether to proceed with Python (py) or Powershell (pw)"
                switch ($option) {
                    'py' { 
                        Write-Host "`nPython chosen." -ForegroundColor Green
                        python -i $CSV.IPYTHONPATH $CSV.CSVPATH $CSV.JSONPATH
                    }
                    'pw' {
                        Write-Host "`nPowershell chosen." -ForegroundColor Green
                        $Global:CSV = Import-Csv $CSV.CSVPATH
                        Write-Host "CSV imported as `$CSV, exiting CLI."
                        break mainLoop
                    }
                    Default {
                        Write-Host "`nCould not understand request, going to Main Loop" -ForegroundColor Red
                        break
                    }
                }
            }

            Default {
                Write-Host "`nNon-valid flag!" -ForegroundColor Red
            }
        }

    }
}
