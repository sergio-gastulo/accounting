function ValidateCategory() {

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
            Write-Host "`nCould not parse '$key' as a valid key. Running this again."
        }

    } while ($true)

    return $tempCategory
}


ValidateCategory