# accounting


## **Description**  
A *really simple* CLI tool to help you track accounting information from the terminal. *(Windows only)*.  


## **Installation**  
1. Clone the repository into a directory included in your PowerShell module path (`$Env:PSModulePath`).  
   - More details on PowerShell module paths can be found in the [official documentation](https://learn.microsoft.com/es-es/powershell/module/microsoft.powershell.core/about/about_psmodulepath?view=powershell-7.5).
	- I would recommend creating a `~\.powershell` module, add said path to `$Env:PSModulePath` and clone the repo there. 
2. Run the following commands in PowerShell:
   ```powershell
   git clone https://github.com/sergio-gastulo/accounting.git
   vim config-example.json # edit file
   Rename-Item config-example.json config.json
   vim fields-example.json # edit file
   Rename-Item fields-example.json fields.json
   Import-Module accounting
   AccountingCommandLineInterface <action> # or acccli <action>
   ```
3. If there are python-dependencies issues, don't worry:
	```
	cd /path/to/cloned/repo/acc_py
	poetry install
	```
	FYI: [poetry](https://python-poetry.org/) must be installed.

### config.json
Check config-example.json for an up-to-date example.

### fields.json
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

## **TODO**
- Provide support for several p1() periods (comparings periods).
- Think of conversion plots.
- Provide support to dump-save python objects. 
- Dump valid ctx for faster import (check if file was edited before).
- Implement duplicate of record (This allows faster writing methods, remember to forget ID since it's a 'duplicate').
- Change errors to what they actually represent (better error printing).
- After parsing, allow config.json to be saved from ctx.
- Expose date parser to construct dates from user input on python REPL.
- When returning dataframe, pd.to_datetime should be called to cast dates automatically.
- When writing conversion, print message showing help should make clearer what is base and target currency.
- Decide whether currencies should be upper or lower case.


### User Compatible TODOs
TODOs that would be useful if this project became an application for other people.
- Provide a saving option for every plot to prevent terminal from hanging when displaying plot.
- Full config.json support (all customizable).
- Flush to stdout so terminal does not polute with user input validation. 
- Provide toy files as examples.
- Add interactive clicks on scatters
- Provide support for changing fields.json
- Provide support for configuring paths from Command Line (probably openning File Browser?).

### Need to elaborate // or discarded
- Provide light-mode support on plot.py.
- Provide WhatsApp message parsing.
- Provide better printing for [read_conversion()](/acc_py/src/acc_py/db/db_api.py).


## **Requirements**:
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
PS C:\> sqlite3.exe --version
3.50.2 2025-06-28 14:00:48 2af157d77fb1304a74176eaee7fbc7c7e932d946bf25325e9c26c91db19e3079 (64-bit)
```

## Credits // other devs projects
- Thanks to [@fawazahmed0](https://github.com/fawazahmed0) for providing such an [open-source amazing API](https://github.com/fawazahmed0/exchange-api).
