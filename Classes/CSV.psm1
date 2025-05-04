using module .\CSVRow.psm1

class CSV {
    [string]    $CSVPATH
    [string]    $JSONPATH
    [string]    $PYTHONSCRIPTPATH


    CSV([string] $csvpath, [string] $jsonpath, [string] $pythonpath) {
        $this.CSVPATH = $csvpath
        $this.JSONPATH = $jsonpath
        $this.PYTHONSCRIPTPATH = $pythonpath
    }

    [int] ValidateInteger( [string] $validation, [int] $bound) {
        $tempInt = 0
        do {
            $temp = Read-Host "`nSelect number of installments"
            try {
                $tempInt = [int]$temp
                if ($tempInt -gt $bound) {
                    break
                } else {
                    Write-Host "`n$validation must be an integer greater than $bound." -ForegroundColor Red
                }            
            } catch {
                Write-Host "`nCould not parse '$temp' as integer. " -ForegroundColor Red
            }
        } while ($true)
    
        Write-Host "`n$validation parsed successfully: '$tempInt'" -ForegroundColor Green
        return $tempInt
    }
    
    [Void] Read(){
        
        $numberOfLines = $this.ValidateInteger("Lines to read", 1)
        Write-Host "`n"
        Get-Content -Path ($this.CSVPATH) -Tail $numberOfLines | Write-Host
        Write-Host "`n"

    }

    [Void] Write([CSVRow]$data){

        if (($data.Amount -gt 200) -and -not ($data.Category -in @("BLIND","INGRESO-SOLES","INGRESO-USD"))) {

            $installments = $this.ValidateInteger("Installments", 1)
            $data.Amount = $data.Amount / $installments

            for ($i = 0; $i -lt $installments; $i++) {
                $tempData = $data.Copy()

                $tempdata.Date = $data.Date.AddMonths($i)
                $tempData.Description = "$($data.Description) tag: cuota $i"
                Add-Content -Path ($this.CSVPATH) -Value ($tempData.Parse())
                if ($i -eq $installments - 1) {
                    Write-Host "`nSeveral lines have been written to file. Sample: $($tempData.Parse())"
                }
            }

        } else {
            Add-Content -Path ($this.CSVPATH) -Value ($data.Parse())
        }
        Write-Host "`nThe following line has been written to file: `n$($data.Parse())" -ForegroundColor Blue
        Write-Host "`nData added." -ForegroundColor Green
    }

    [void] Plot(){
        python $this.PYTHONSCRIPTPATH $this.CSVPATH $this.JSONPATH | ForEach-Object {
            Write-Host $_
        }
    }

    [System.Collections.Specialized.OrderedDictionary] GetJSON() {
            
        $psobject = Get-Content ($this.JSONPATH) -Raw | ConvertFrom-Json
        
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