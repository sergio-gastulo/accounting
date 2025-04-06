function ValidateDescription {
    $description = ''
    
    do {
        $description = Read-Host "`nType description. No commas."
        if ($description -notmatch ',') {
            break
        }
        Write-Host "`nDescription must not include comma (,)."
    } while ($true)

    return $description
}

ValidateDescription