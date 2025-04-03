using System;

class Program
{
    static void Main()
    {
        CSVRow element = new CSVRow(DateTime.Now, 0.1, "2", "3");
        element.Print();
    }
};