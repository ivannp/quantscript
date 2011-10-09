#!/bin/sh

# The required paramters are:
#     $1: The user name for eoddata
#     $2: The password for eoddata
#     $3: The from email for the notification
#     $4: The to email for the notification
#     $5: The gmail user for the notification
#     $6: The gmail password for the user
#     $7: The "working" directory
#     $8: The path to the daily R workhorse and output

# Switch to the working directory
cd $7

echo "========================="
date

echo "Downloading data ..."
python eoddata.py --verbose --download-daily --user $1 --password $2

echo "Updating the database ..."
python eoddata.py --verbose --add-daily

echo "Extracting the interesting symbols ..."
python eoddata.py --verbose --extract-symbols

# Switch to the R script directory
cd $8

# Generate the output file name
output=R.output.`date +'%y%m%d'`

# Run R
echo "Running the R magic ..."
R CMD BATCH daily.R $output

# Switch back to the working directory
cd $7

# Send the email
echo "Sending the email ..."
python sendEmail.py --subject "Daily Signals" --from $3 --to $4 --c $8/$output --user $5 --password $6

echo "=========================\n\n"
