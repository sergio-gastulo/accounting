# accounting

## **Description**  
A *really simple* CLI tool to help you track accounting information from the terminal. *(Windows only)*.  

## **Installation**  
1. Clone the repository into a directory included in your PowerShell module path (`$Env:PSModulePath`).  
   - More details on PowerShell module paths can be found in the [official documentation](https://learn.microsoft.com/es-es/powershell/module/microsoft.powershell.core/about/about_psmodulepath?view=powershell-7.5).  

2. Run the following commands in PowerShell:
   ```powershell
   git clone https://github.com/sergio-gastulo/accounting.git
   vim accounting.psm1 # edit head of file
   Import-Module accounting
   AccountingCommandLineInterface <action> # or acccli <action>
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
* help (string) – Full explanation or tooltip-style guidance.
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

## TODO

### Urgent

### Suggestions
- Implement support for transactions (from currency CU1 to CU2)
- Provide WhatsApp message parsing.
- `category_time_series` should dash the horizontal line.
- `monthly_time_series` could fail better (if one plot fails, then all the plot fails, this should not happen).
- `parse_semantic_filter` could do better for dates: provide support for `today`, `yesterday`, `+/-int`, etc.
- Modifications to `db` could provide a before and after when comitting. 
- Provide support for changing fields.json
- Provide support for configuring paths from Command Line (probably openning File Browser?).
- [context.py](/acc_py/src/acc_py/context/context.py) should load from such config file.
- Provide support for non-recognizable binaries (e.g. python doesn't exist, sqlite3 doesn't exist, etc.)
- Provide toy files as examples.
- `write_list` should show id upon correct parsing, so it can be quickly edited.
- "description" could be bound to some characters when printing. 
- parse_semantic_filter should be able to provide help menu.
- It should be possible to import `plot` functionality when dealing with db (or viceversa)
- Provide offline support.
- Help for `r` is broken.
- Help for `r` should print the parser help message as well.
- Provide support for semantic filter: given a single id x, return records such that id in [x-r, x + r].
- When priting SQL records, description should have a limit. 



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

## Credits
- Thanks to [@fawazahmed0](https://github.com/fawazahmed0) for providing such an amazing API: [https://github.com/fawazahmed0/exchange-api]
