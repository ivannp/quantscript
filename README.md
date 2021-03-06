# Quantscript

## Introduction
This project contains some tools I used on daily basis to automate my trading decisions. These tools are build around the data provider I used back in the day - www.eoddata.com. Alghough I have moved since and am not running the code on a daily basis, I still find it a valuable example each time I have to code a new script, especially with Python.

The daily workflow was simple:

1. Download the data for the last few days from ftp.eoddata.com
2. Add the downloaded data to the database
3. Run the workhorse R script to analyze the instruments I am trading
4. Send an email to me with the output of the previous step
5. All this is run once a day from a unix cron job.

## The Source Code
All communications with www.eoddata.com and all database related activities are executed through the **eoddata.py** script. The configuration is read from **eoddata.ini**. I hope it's self explanatory.

Besides downloading data and updating the database, **eoddata.py** can be used for several other tasks, for example, to rebuild a single exchange from long term (usually 20 years) of historic data. www.eoddata.com provides the long term history data in zip files and the script supports them directly.

**sendEmail.py** is exactly that - to send an email using gmail.

The project also contains **daily.sh** which is the script I run from my cron job. This script takes many arguments, like username, password for ftp.eoddata.com, so that nothing is exposed in user files. My password is present only in the cron configuration files.

One more file worth mentioning - **eoddata.R**, which contains utility functions to ease a few R tasks.

## The Database
The database structure is very simple at the moment. For each exchange from the ini file, there is a table. The table has the following format:

**Symbol, Timestamp, Open, High, Low, Close, Volume**

## The Data
There are three types of data with respect to the subscription one gets.

1. The historical stock data (which I call the long-term history) is purchased on exchange by exchange basis. It goes back about 20 years, back to 1991 usually. The only way to download the data is to use the web interface. It comes in zip files, one zip file for each year. The naming follows the format NYSE_1998.zip. A five year history of NYSE is provided for free.
2. The daily data is accessible only by the monthly subscribers. It is available in the main directory on ftp.eoddata.com. For each exchange, there are csv files with the data going back about 5 days.
3. What I call the short-term history data is historical data for each exchange. How far this data goes back varies depending on the subscription, for Gold members it goes back one year. This data is available from ftp://ftp.eoddata.com/History in csv format.

## Using eoddata.py
This script is the interface to the www.eoddata.com and to the database. The configuration is loaded from **eoddata.ini**. Different command line options are provided for the supported operations.

## Adding Long Term History Data
Let's assume we have purchased 20 years of history for COMEX. All the zip files (COMEX_1991.zip to COMEX_2011.zip) are downloaded in the comex/ subfolfder. If we want to add all the zip files to the database, we run:

```
python eoddata.py --verbose --add-zip --exchange COMEX comex/COMEX_*zip
python eoddata.py --verbose --replace --add-zip --exchange COMEX comex/COMEX_*zip
```

When the market data for a particular timestamp is already in the database, the default action is to skip (IGNORE in the SQL syntax) the change. The replace option tells the script to replace any existing data with the file contents.

Of course, we should have configured the COMEX exchange in the **eoddata.ini** file.

Another option is to rebuild the data for the comex exchange. This drops and creates the table for the exchange and then loads the data.

```
python eoddata.py --verbose --build-exchange COMEX
```

Notice that the location of the zip files does not have to be provided on the command line - the default location is configured in eoddata.ini, namely the value of the Dir setting under the exchange section. All *zip files under this location are used to build the exchange.

Last, one can rebuild all configured exchanges at once.

```
python eoddata.py --verbose --build-exchanges
```

## Adding Short Term History Data
The long term history data usually does not contain the last about 20 days. Neither does the daily data - it goes back about five days. This is when the short-term history data comes into play.

```
python eoddata.py --verbose --download-history --since 20110122 --user theUser --password thePassword
```

Since I noticed that the long term history goes back to 20110123, I don't want the short term history to be downloading the files much before that date - the since option.

Then we need to add this history to the database.

```
python eoddata.py --verbose --add-history
```

## Adding the Daily Data
The commands to download and add the daily data are similar to the handling of the short term history data. The since option is not supported however.

```
python eoddata.py --verbose --download-daily --user theUser --password thePassword
python eoddata.py --verbose --add-daily
```

## Vacuuming the Database
It is a good idea to vacuum the database after a significant re-organizaiton and also once in a while just in case. The vacuuming clusters the data and indexes, which typically helps performance. The vacuuming is done using the sqlite3 command line utility and its prompt.

```
sqlite3 eoddata.sqlite 
SQLite version 3.7.2
Enter ".help" for instructions
Enter SQL statements terminated with a ";"
sqlite> vacuum;
sqlite> .exit
```
