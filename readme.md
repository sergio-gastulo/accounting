# accounting

## **Description**  
A *really simple* CLI tool to help you track accounting information from the terminal. *(Windows only)*.  

## **Installation**  

1. Clone the repository into a directory included in your PowerShell module path (`$Env:PSModulePath`).  
   - More details on PowerShell module paths can be found in the [official documentation](https://learn.microsoft.com/es-es/powershell/module/microsoft.powershell.core/about/about_psmodulepath?view=powershell-7.5).  

2. Run the following commands in PowerShell:  
   ```powershell
   git clone https://github.com/sergio-gastulo/accounting.git
   vim accounting.psm1 # edit [CSV]::new()
   Import-Module accounting
   AccountingCommandLineInterface # acccli
   ```

## TODO:
- When prompting for integers, it should be able to prompt basic aritmethic operations. E.g., "1+1" should evaluate to 2. 
- Aggregate the following options: `c` for clearing the console, `f` for filtering, and `r` for returning the CSV ready to be filtered under pandas (`python -i -c "string"`) or powershell (continuing on the terminal), `h` for listing all available categories.
- Refactor JSON since its structure sucks.

## Requirements:
This project was built with `powershell` and `python`.
1. `powershell` version
```
PS C:\> $PSVersionTable.PSVersion

Major  Minor  Build  Revision
-----  -----  -----  --------
5      1      26100  3624
```
2. `python` dependencies
```
PS C:\> python --version
Python 3.12.3
PS C:\> "json", "pandas", "matplotlib" | % {python -c "import $_; print(f'$_ : {$_.__version__}')"}
json : 2.0.9
pandas : 2.2.2
matplotlib : 3.8.4
```
