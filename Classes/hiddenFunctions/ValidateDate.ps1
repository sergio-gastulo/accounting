function ValidateDate() {
    $tempDate = (Get-Date)
    while($true){
        $day = Read-Host "`nInsert a day"
        $month = Read-Host "`nInsert a month"
        try {
            $tempDate = Get-Date -Day $day -Month $month
            break
        }
        catch {
            $flag = Read-Host "Running this again, could not parse $day and $month.`nIf you wish to leave and choose today as date, press 'x'. Otherwise, press any button"
            if($flag -eq 'x'){
                break
            }
        }
    }
    return $tempDate
}

ValidateDate
