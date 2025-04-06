function ValidateCategory() {

    $categoryDict = [ordered]@{

        bl = 'BLIND'
        
        cas = [ordered]@{
            ga = 'CASA-GASTO'
            gi = 'CASA-GIFT'
        }

        cel = 'CELULAR'

        com = [ordered]@{    
            ag = 'COMIDA-AGUA'
            sa = 'COMIDA-SALIR'
            sn = 'COMIDA-SNACK'
            tr = 'COMIDA-TRAGO'
        }
            
        ed = 'EDUCATION'

        gi = 'GIFTS'

        ing = [ordered]@{
            s = 'INGRESO-SOLES'
            u = 'INGRESO-USD'
        }

        im = 'IMPUESTOS'

        pas = 'PASAJE'

        per = 'PERDIDO'

        perso = [ordered]@{
            f = 'PERSONAL-FIX'
            g = 'PERSONAL-GYM'
            h = 'PERSONAL-HEALTH'
            r = 'PERSONAL-REGALO'
            tall = 'PERSONAL-TALLER'
            tram = 'PERSONAL-TRAM' #TRAMITE
        }
        
        pet = 'PETS'

        sal = 'SALIDA'

        sub = 'SUBSCRIPTIONS'

        var = 'VARIOS'

        xch = [ordered]@{
            su = 'SOLES-USD'
            us = 'USD-SOLES'
        }
    }

    $tempCategory= ""

    :CategoryLoop do {
        Write-Host "["
        $categoryDict.Keys | ForEach-Object { "`t$_" } | Write-Host -Separator ",`n"
        Write-Host "]"
        $key = Read-Host "`nSelect a key from the dictionary above"
        $temp = $categoryDict[$key]        

        if ($temp -is [System.Collections.Specialized.OrderedDictionary]) {            
            $temp | ConvertTo-Json | Write-Host
            :subCategoryLoop do{
                $tempSubCategory = Read-Host "`nKey belongs to Ordered Dictionary. Please select a key"
                if($temp[$tempSubCategory]){
                    $tempCategory = $temp[$tempSubCategory]
                    break subCategoryLoop
                } else {
                    Write-Host "`nUnrecognized subkey. Loop running again." -ForegroundColor Red
                    $temp | ConvertTo-Json | Write-Host
                }
            }while($true)
            
            break CategoryLoop

        } elseif ($temp -is [string]) {
            $tempCategory = $temp
            Write-Host "`nCategory parsed succesfully: '$tempCategory'"
            break CategoryLoop
        } else {
            Write-Host "`nCould not parse '$key'. Loop running again." -ForegroundColor Red
        }
    } while($true)

    return $tempCategory
}

ValidateCategory