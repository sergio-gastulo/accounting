# accounting

## Description

A *really* simple CLI that can help you track accounting information from the terminal. 

## Installation

Clone the repository on a directory that is in your Powershell Module's Path environment `$Env:PSModulePath`. Further info can be found [here](https://learn.microsoft.com/es-es/powershell/module/microsoft.powershell.core/about/about_psmodulepath?view=powershell-7.5).

```
git clone https://github.com/sergio-gastulo/accounting.git
Import-Module accounting
AccountingCommandLineInterface 
```

## TODO:
    - Update $categoryDict so it can load from a JSON from some .env directory. 
    - A decent plot function that relies in a standalone application without openning any other app.