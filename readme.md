# accounting


## **Description**  
A *really simple* CLI tool to help you track accounting information from the terminal. *(Windows only)*.  


## **Installation**  
1. Clone the repository into a directory included in your PowerShell module path (`$Env:PSModulePath`).  
   - More details on PowerShell module paths can be found in the [official documentation](https://learn.microsoft.com/es-es/powershell/module/microsoft.powershell.core/about/about_psmodulepath?view=powershell-7.5).
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
3. To install dependencies:
	```
	cd /path/to/cloned/repo/acc_py
	uv pip install -r pyproject.toml
	```
	FYI: [uv](https://docs.astral.sh/uv/) must be installed.

### config.json
It carries simple configurations like the path to the database, which currencies are being managed and some matplotlib configurations.
Check [config-example.json](/config/config-example.json) for an up-to-date example.

### fields.json
It defines a list of categories. Each category contains basic metadata, and optionally, subcategories. Field Descriptions: 
* key (string) - Unique identifier for the category.
* shortname (string) - A brief display name.
* description (string) - A longer label or description for the category.
* help (string) - Full explanation or tooltip-style guidance.
* subcategories (array of key-value pairs, optional) - Nested categories that follow the same structure.
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
Check [fields-example.json](/config/fields-example.json) for an up-to-date example.

## **TODO**
- Decide whether currencies should be upper or lower case.
- Check plots are light/dark mode responsive up to user configurations.
- `fetch` should return dataframe with pd.to_datetime .

### User Compatible TODOs
TODOs that would be useful if this project became an application for other people.
- Provide a saving option for every plot to prevent terminal from hanging when displaying plot.
- Flush to stdout so terminal does not polute with user input validation. 
- Provide toy files as examples.
- Provide support for changing fields.json
- Provide support for configuring paths from Command Line (probably openning File Browser?).

### Need to elaborate
- Think of conversion plots.
- Provide WhatsApp message parsing.
- When returning dataframe, pd.to_datetime should be called to cast dates automatically (i.e., fix bug on datetime calls and csv casting) (I haven't reproduced this in a while tbh).


## **Requirements**:
This project was built with `powershell`, `python`, and `sqlite`.
1. `powershell` version
```
PS C:\> $PSVersionTable.PSVersion

Major  Minor  Build  Revision
-----  -----  -----  --------
5      1      26100  3624
```
2. For `python` dependencies, check [`pyproject.toml`](/acc_py/pyproject.toml).

3. `sqlite`:
```
PS C:\> sqlite3.exe --version
3.50.2 2025-06-28 14:00:48 2af157d77fb1304a74176eaee7fbc7c7e932d946bf25325e9c26c91db19e3079 (64-bit)
```

## Credits // other devs projects
- Thanks to [@fawazahmed0](https://github.com/fawazahmed0) for providing such an [open-source amazing API](https://github.com/fawazahmed0/exchange-api).
