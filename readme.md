# accounting

## **Description**  
A *really simple* CLI tool to help you track accounting information from the terminal. *(Windows only)*.  

## **Installation**  

1. Clone the repository into a directory included in your PowerShell module path (`$Env:PSModulePath`).  
   - More details on PowerShell module paths can be found in the [official documentation](https://learn.microsoft.com/es-es/powershell/module/microsoft.powershell.core/about/about_psmodulepath?view=powershell-7.5).  

2. Run the following commands in PowerShell:  
   ```powershell
   git clone https://github.com/sergio-gastulo/accounting.git
   Import-Module accounting
   AccountingCommandLineInterface
   ```

3. Don't forget to add a custom `.csv` where records will be written.

## TODO:
    - Update $categoryDict to load from a JSON stored in some sort of .env directory. 
    - Implement a standalone plotting function that doesn’t require opening an external application (less overhead).