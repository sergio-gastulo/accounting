using System;

class date_validation
{
    static void Main()
    {
        string stringToParse = Console.ReadLine();
        Console.WriteLine(stringToParse);

        string[] dayMonth = stringToParse.Split(' ');

        if (dayMonth.Length == 2)
        {
            Console.WriteLine("Day Month");
        } 
        else if (dayMonth.Length == 1 ) 
        {
            Console.WriteLine("Day");
        } 
        else 
        {
            Console.WriteLine("Sorry, this could not be parsed");
        }

    }
}