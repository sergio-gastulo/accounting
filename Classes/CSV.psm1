using module .\CSVRow.psm1

class CSV {
    [string]    $CSVPATH
    [System.Collections.Specialized.OrderedDictionary]    $JSONDICT


    CSV([string] $csvpath, [string] $jsonpath) {
        $this.CSVPATH = $csvpath
        $this.JSONDICT = GetJSON($jsonpath)
    }

    [int] ValidateInstallments() {
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
    
    [Void] Read(){
        
        $numberOfLines = Read-Host "`nInsert number of lines to be read"
        Get-Content -Path ($this.CSVPATH) -Tail $numberOfLines | Write-Host

    }

    [Void] Write([CSVRow]$data){

        if (($data.Amount -gt 200) -and -not ($data.Category -in @("BLIND","INGRESO-SOLES","INGRESO-USD"))) {

            $installments = $this.ValidateInstallments()
            $data.Amount = $data.Amount / $installments

            for ($i = 0; $i -lt $installments; $i++) {
                $tempData = $data.Copy()

                $tempdata.Date = $data.Date.AddMonths($i)                
                $tempData.Description = "$($data.Description) tag: cuota $i"
                Add-Content -Path ($this.CSVPATH) -Value ($tempData.Parse())
            }
        } else {
            Add-Content -Path ($this.CSVPATH) -Value ($data.Parse())
        }
        Write-Host "`nData added." -ForegroundColor Blue
    }

    [void] Plot(){
        Write-Host "Plotting data."
    }

    [System.Collections.Specialized.OrderedDictionary] GetJSON([string] $path) {
            
        $psobject = Get-Content ($path) -Raw | ConvertFrom-Json
        
        $dictionary = [ordered]@{}
        
        $keys = $psobject.psobject.properties.Name
    
        function Get-Hashtable {
            [OutputType([System.Collections.Specialized.OrderedDictionary])]
            param(
                [psobject] $psobj
                )
                
                $hashtable = [ordered]@{}
                $psobj.psobject.properties | ForEach-Object {$hashtable[$_.Name] = $_.Value.shortname} 
                return $hashtable
                
            }
        
        $keys | ForEach-Object {
            if ($psobject.$_.shortname) {
                $dictionary[$_] = $psobject.$_.shortname
            } else {
                $dictionary[$_] = Get-Hashtable ($psobject.$_)
            }
        }
        
        return $dictionary
            
    }

}