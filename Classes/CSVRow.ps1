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
            $tempDescription = Read-Host "`nType description. No commas."
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

}

$data = [CSVRow]::new()

$data.Print()




