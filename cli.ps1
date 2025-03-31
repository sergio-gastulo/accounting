class CSVRow {
    [datetime]  $Date
    [Double]    $Amount
    [String]    $Category
    [String]    $Description 
    
    CSVRow () {
        $this.Date = $this.ValidateDate() 
        $this.Amount = $this.ValidateAmount() 
        $this.Description = $this.ValidateDescription()
        $this.Category = $this.ValidateCategory()
    }

    CSVRow([datetime]$Date, [double]$Amount, [string]$Category, [string]$Description) {
        $this.Date = $Date
        $this.Amount = $Amount
        $this.Category = $Category
        $this.Description = $Description
    }
    
    hidden [datetime] ValidateDate() {
        $tempDate = (Get-Date)
        
        while($true){
            $period = Read-Host "`nInsert (day) or (day month)"
            
            try {
                $day, $month = $period.Split(" ")
                if($month){
                    $tempDate = Get-Date -day $day -month $month
                } else {
                    $tempDate = Get-Date -day $day
                }
                break
            } catch {
                $flag = Read-Host "Running this again, could not parse '$period'. Use Date=Today? (y/press anything)" -ForegroundColor Red
                if ($flag -eq 'y') {
                    break
                }
            }
        }
        Write-Host "`nParse successfull: '$($tempDate.ToString("dddd, MMMM d, yyyy"))'" -ForegroundColor Blue
        return $tempDate
    }

    hidden [double] ValidateAmount() {
        $namount = 0.0
        do {
            $tempAmount = (Read-Host "`nInsert expense")
            try {
                $namount = [double]$tempAmount
                if ($namount -gt 0.0) {
                    break
                } else {
                    Write-Host "`n$tempAmount must be a positive integer." -ForegroundColor Red
                }
            }
            catch {
                Write-Host "`nRunning this again, $tempAmount could not be parsed to Double" -ForegroundColor Red
            }
        } while ($true)
        Write-Host "`nParse successfull: '$namount'" -ForegroundColor Blue
        return $namount
    }

    hidden [String] ValidateDescription() {
        $tempDescription = ''
        
        do {
            $tempDescription = Read-Host "`nType description -- no commas"
            if ($tempDescription -notmatch ',') {
                break
            }
            Write-Host "`nDescription cannot include comma (,)." -ForegroundColor Red
        } while ($true)
        Write-Host "`n Succcessfull parse: '$tempDescription'" -ForegroundColor Blue
        return $tempDescription
    }

    hidden [String] ValidateCategory() {

        $categoryDict = [ordered]@{
            bl      =   'BLIND'
            cas     =   'CASA'
            cel     =   'CELULAR'
            cvar    =   'COM_VAR'
            ing     =   'INGRESO'
            men     =   'MENU'
            pas     =   'PASAJE'
            per     =   'PERSONAL'
            rec     =   'RECIBO'
            usd     =   'USD_INC'
            var     =   'VARIOS'
        }
    
        $tempCategory= ""
        
        do {
            $categoryDict | ConvertTo-Json | Write-Host
            $key = Read-Host "`nSelect a key from the dictionary above"
            $tempCategory = $categoryDict[$key]
    
            if($tempCategory){
                break
            } else {
                Write-Host "`nCould not parse '$key' as a valid key. Running this again." -ForegroundColor Red
            }
    
        } while ($true)
        Write-Host "`nKey found successfully: '$tempCategory'" -ForegroundColor Blue
        return $tempCategory
    }

    [String]Parse(){

        return @(
            $this.Date.ToString("dd-MM-yyyy"),
            $this.Amount,
            $this.Description,
            $this.Category
        ) -join ","

    }

    [Void]Print(){
        Write-Host @"
Date:        $($this.Date.ToString("dd-MM-yyyy"))
Amount:      $($this.Amount)
Description: $($this.Description)
Category:    $($this.Category)
"@
    }

    [CSVRow] Copy(){
        return [CSVRow]::new($this.Date, $this.Amount, $this.Category, $this.Description)
    }

}

class CSV {
    static [String]$CSVPATH = "C:\Users\sgast\PROJECTS\Modules\accounting\cuentas.csv"

    static [int] ValidateInstallments() {
        $tempInt = 0
        do {
            $temp = Read-Host "`nSelect number of installments"
            try {
                $tempInt = [int]$temp
                if ($tempInt -gt 1) {
                    break
                } else {
                    Write-Host "`nInstallments must be an integer greater than 1." -ForegroundColor Red
                }            
            } catch {
                Write-Host "`nCould not parse '$temp' to Integer. Running this again." -ForegroundColor Red
            }
        } while ($true)
    
        Write-Host "`nInstallments parsed successfully: '$tempInt'" -ForegroundColor Blue
        return $tempInt
    }
    
    static [Void] Read(){
        
        $numberOfLines = Read-Host "`nInsert number of lines to be read"
        Get-Content -Path ([CSV]::CSVPATH) -Tail $numberOfLines | Write-Host

    }

    static [Void] Write([CSVRow]$data){

        if (($data.Amount -gt 200) -and -not ($data.Category -in @("BLIND","INGRESO","USD_INC"))) {

            $installments = [CSV]::ValidateInstallments()
            $data.Amount = $data.Amount / $installments

            for ($i = 0; $i -lt $installments; $i++) {
                $tempData = $data.Copy()

                $tempdata.Date = $data.Date.AddMonths($i)                
                $tempData.Description = "$($data.Description) tag: cuota $i"
                Add-Content -Path ([CSV]::CSVPATH) -Value ($tempData.Parse())
            }
        } else {
            Add-Content -Path ([CSV]::CSVPATH) -Value ($data.Parse())
        }
        Write-Host "`nData added." -ForegroundColor Blue
    }

    static [void] Plot(){
        Write-Host "Plotting data."
    }
}

function AccountingCLI {
    :mainLoop while ($true) {

        @{
            r   =   'read'
            w   =   'write'
            p   =   'plot'
            q   =   'quit'
        } | ConvertTo-Json -Depth 4

        $action = Read-Host "Please select which action you would like to perform"

        switch ($action) {
            'r' { 
                Write-Host "`nRead Data selected."
                [CSV]::Read()
            }

            'w' { 
                Write-Host "`nWrite Data selected."
                $data = [CSVRow]::new()
                [CSV]::Write($data)
            }

            'p' {
                Write-Host "`nPlotting data."
                [CSV]::Plot()
            }

            'q' {
                Write-Host "`nBreaking Loop. Bye!" -ForegroundColor Blue
                break mainLoop
            }

            Default {
                Write-Host "Non-valid flag" -ForegroundColor Red
            }
        }

    }
}

AccountingCLI