# accounting

## **Description**  
A *really simple* CLI tool to help you track accounting information from the terminal. *(Windows only)*.  

## **Installation**  
1. Clone the repository into a directory included in your PowerShell module path (`$Env:PSModulePath`).  
   - More details on PowerShell module paths can be found in the [official documentation](https://learn.microsoft.com/es-es/powershell/module/microsoft.powershell.core/about/about_psmodulepath?view=powershell-7.5).  

2. Run the following commands in PowerShell:
   ```powershell
   git clone https://github.com/sergio-gastulo/accounting.git
   vim accounting.psm1 # edit accounting.psm1
   Import-Module accounting
   AccountingCommandLineInterface # or 'acccli'
   ```

3. If you have python-dependencies issues, don't worry! You can:
	```
	cd /path/to/cloned/repo/acc_py
	poetry install
	```
	Of course, you must have [poetry](https://python-poetry.org/) installed.

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
- Provide support for passing arguments to main function: `acccli -arg value`. 
- Categories should be sorted when printed in accounting.psm1.
- One could improve how to track installments (some unique UUID?)
- Implement support for transactions (from currency CU1 to CU2)
- Plots should sum the expenses in their respective default currency.
- Provide toy db as an example.
- category_time_series should dash the horizontal line.
- monthly_time_series could fail better.
- Modifications to `db` could provide a before and after when comitting. 
- `pprint` could do a better job.
- `parse_semantic_filter` could do better for dates: provide support for `today`, `yesterday`, `+/-int`, etc.
- `parse_semantic_filter` should allow "and".
- Provide editor support.

## Requirements:
This project was built with `powershell`, `python`, and `sqlite`.
1. `powershell` version
```
PS C:\> $PSVersionTable.PSVersion

Major  Minor  Build  Revision
-----  -----  -----  --------
5      1      26100  3624
```
2. For `python` dependencies, check [`pyproject.toml`](acc_py/pyproject.toml).

3. `sqlite`:
```
sqlite> SELECT sqlite_version();
3.50.2
```

## Recomendations
- In many cases, you spend money in a given currency CU1 but it is discounted from your card in another currency: CU2. I strongly believe one should always use static values when writing to 'db'. For that reason, you can set `$tasa = CU2/CU1` in your global session and it will automatically convert your spendings being writen in CU1 as in CU2. (Unfortunately, you must manually specify `currency = CU2`)`.
