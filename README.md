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

The Database
The database structure is very simple at the moment. For each exchange from the ini file, there is a table. The table has the following format:

**Symbol, Timestamp, Open, High, Low, Close, Volume**
