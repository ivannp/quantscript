# Introduction #

This project contains the tools I use on daily basis to automate my trading decisions. The strategies I use currently in my trading and in my research are based only on end-of-day data (eoddata). The tools are build around my current data provider - **www.eoddata.com**.

The daily workflow is simple:

  1. Download the data for the last few days from **ftp.eoddata.com**
  1. Add the downloaded data to the database
  1. Run the workhorse **R** script to analyze the instruments I am trading
  1. Send an email to me with the output of the previous step

All this is run once a day from a unix cron job.

# The Source Code #
All communications with **www.eoddata.com** and all database related activities are executed through the **eoddata.py** script. The configuration is read from **eoddata.ini**. I hope it's self explanatory.

Besides downloading data and updating the database, **eoddata.py** can be used for several other tasks, for example, to rebuild a single exchange from long term (usually 20 years) of historic data. **www.eoddata.com** provides the long term history data in zip files and the script supports them directly.

**sendEmail.py** is exactly that - to send an email using gmail.

The project also contains **daily.sh** which is the script I run from my cron job. This script takes many arguments, like username, password for **ftp.eoddata.com**, so that nothing is exposed in user files. My password is present only in the cron configuration files.

One more file worth mentioning - **eoddata.R**, which contains utility functions to ease a few R tasks.

# The Database #
The database structure is very simple at the moment. For each exchange from the ini file, there is a table. The table has the following format:

**Symbol, Timestamp,  Open, High, Low, Close, Volume**

# Organizational Links #
  * StoryList
  * AlgorithmDescriptions