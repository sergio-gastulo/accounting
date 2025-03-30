function ValidateDate() {
    $tempDate = (Get-Date)
    
    while($true){
        $period = Read-Host "`nInsert a (day month).`nIf month is not specified, it will be assumend to be this month"
        
        try {
            $day, $month = $period.Split(" ")
            if($month){
                $tempDate = Get-Date -day $day -month $month
            } else {
                $tempDate = Get-Date -day $day
            }
            break
        } catch {
            $flag = Read-Host "Running this again, could not parse '$period'. Use Date=Today? (y/press anything)"
            if ($flag -eq 'y') {
                break
            }
        }
    }
    return $tempDate
}

ValidateDate
