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

### JSON Structure
It defines a list of categories. Each category contains basic metadata, and optionally, subcategories. Field Descriptions: 
* key (string) – Unique identifier for the category.
* shortname (string) – A brief display name.
* description (string) – A longer label or description for the category.
* help (string) – Full explanation or tooltip-style guidance for users.
* subcategories (array of json's, optional) – Nested categories that follow the same structure.
```js
[
   {
		"key":"your key",
		"shortname":"short name",
		"description":"long description",
		"help":"complete description"
	},
	{
		"key":"another key",
		"shortname":...,
		"description":...,
		"help":...,
		"subcategories":[
			{
				"key":"sub key",
				"shortname":...,
				"description":...,
				"help":...,
         	},
			...
		]
	}
]
```

## TODO:
- Python interactivity when plotting could be improved in general.
- Add arguments to main function `acccli arg option`. 
- Re-factor python: should ask `period` only at the beginning and should be more readable (implemented but still needs fixes).
- Refactor plot. We are should not be using `read_csv`. 
- Rename modules: We migrated from CSV to SQLITE, we must re-name modules and stuff: `$CSV`, `$CSVRow` seems pretty useless now. 
- Categories should be sorted when printed. 
- One could improve how to track payings in installments (some unique UUID?)

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
