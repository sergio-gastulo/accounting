function ValidateCategory{

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

    $category = ""
    
    do {
        $categoryDict | ConvertTo-Json
        $key = Read-Host "`nSelect a key from the dictionary above"
        if ($categoryDict.ContainsKey($key)) {
            $category = $categoryDict[$key]
            break
        } else {
            Write-Host "`nInvalid key, please try again."
        }
    } while ($true)

    return $category
}


ValidateCategory