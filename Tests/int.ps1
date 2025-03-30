class mySpecifiedClass {
    [datetime]  $Date
    [Double]    $Amount
    [String]    $Category
    [String]    $Description

    mySpecifiedClass() {
        $this.Date = (Get-Date)
        $this.Amount = 0
        $this.Category = "BLIND"
        $this.Description = "test"
    }

}


class ExampleBook2 {
    [string]   $Name
    [string]   $Author
    [int]      $Pages
    [datetime] $PublishedOn

    ExampleBook2() {
        $this.PublishedOn = (Get-Date).Date
        $this.Pages       = 1
    }
}