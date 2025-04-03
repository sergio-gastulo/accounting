using System;

public class CSVRow
{
    private DateTime datetime;
    private double amount;
    private string description;
    private string category; 

    public CSVRow(DateTime datetime, double amount, string description, string category)
    {
        this.datetime       =   datetime;
        this.amount         =   amount;
        this.description    =   description;
        this.category       =   category;
    }

    public void Print()
    {
        Console.Write(string.Join(",", new [] {
            this.datetime.ToString(), 
            this.amount.ToString(), 
            this.description, 
            this.category}));
    }

};