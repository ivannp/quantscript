import os
import sys
import datetime
import sqlite3
import optparse
import csv
import glob
import ConfigParser
import tempfile
import fnmatch
import zipfile
import shutil
import ftplib

options = None
args = None
config = None

def extractSymbol(symbol, exchange):

   """
   Extracts all the data for a given EXCHANGE/SYMBOL combination to the
   standard output.  The exchange parameter is needed to decide which table
   to query.
   """

   global config, options

   dbPath = config.get('General', 'DbPath')
   tableName = config.get(exchange, "Table")
   
   con = sqlite3.connect(dbPath)
   cursor = con.cursor()
   
   cursor.execute('select timestamp, open, high, low, close, volume from ' + tableName + ' where symbol = \'' + symbol + '\' order by timestamp')
   for row in cursor:
      print( str(row[0]) + ',' + str(row[1]) + ',' + str(row[2]) + ',' + str(row[3]) + ',' + str(row[4]) + ',' + str(row[5]))
      
   con.commit()
   cursor.close()
   

def extractExchangeSymbols(exchange):

   """
   Extracts all "interesting" symbols for an exchange.  The interesting symbols
   and the corresponding output files are read from the .ini file, more
   specifically from the corresponding [EXCHANGE Symbols] section.

   For example, if exchange == "COMEX" and the .ini file contains:

   [COMEX]
   Dir: comex

   [COMEX Symbols]
   GC: gc.csv
   SI: si.csv

   Then the function will extract the data for GC and SI symbols, storing the
   output to comex/gc.csv and comex/si.csv files, respectively.  As you can see
   the output files are relative to the directory defined for the exchange.
   """

   global config, options

   dbPath = config.get('General', 'DbPath')
   tableName = config.get(exchange, "Table")
   dir = config.get(exchange, "Dir")
   
   symbols = config.items(exchange + " Symbols")
   
   con = sqlite3.connect(dbPath)
   cursor = con.cursor()
   
   for ss in symbols:
      ff = open(os.path.join(dir, ss[1]), 'w')
      cursor.execute('select timestamp, open, high, low, close, volume from ' + tableName + ' where symbol = \'' + ss[0] + '\' order by timestamp')
      for row in cursor:
         ff.write( str(row[0]) + ',' + str(row[1]) + ',' + str(row[2]) + ',' + str(row[3]) + ',' + str(row[4]) + ',' + str(row[5]) + '\n')
      ff.close()
      
   con.commit()
   cursor.close()
   
def addExchangeFiles(exchange, filePaths):
   
   """
   Add a list of files for a particular exchange into the database. The input
   files are supposed to be in csv format.
   """
   
   global config, options
   
   dbPath = config.get('General', 'DbPath')
   tableName = config.get(exchange, 'Table')
   try:
      removeSuffix = config.get(exchange, 'RemoveSuffix')
   except ConfigParser.NoOptionError:
      removeSuffix = ''

   con = sqlite3.connect(dbPath)
   cursor = con.cursor()
   
   cursor.execute('create table if not exists ' + tableName + ' (symbol text, timestamp text, open float, high float, low float, close float, volume integer, constraint indexes_id primary key (symbol, timestamp))')
   con.commit()
   
   if options.replace:
      cmd = 'insert or replace into ' + tableName + ' '
   else:
      cmd = 'insert or ignore into ' + tableName + ' '
   
   for filePath in filePaths:
      if options.verbose:
         print 'Processing ' + filePath

      reader = csv.reader(open(filePath), delimiter=',')

      if options.header:
         reader.next()
         
      readDataLine = False

      for row in reader:
         if removeSuffix and row[0].endswith(removeSuffix):
            symbol = row[0][:-len(removeSuffix)]
         else:
            symbol = row[0]

         format = '%d-%b-%Y'
         try:
            date = datetime.datetime.strptime(row[1], format).date()
         except ValueError:
            format = '%Y%m%d'

         # If we have already seen a line with data - break the program if the second
         # parsing fails, otherwise assume we are cycling through header lines
         if readDataLine:
            date = datetime.datetime.strptime(row[1], format).date()
         else:
            try:
               date = datetime.datetime.strptime(row[1], format).date()
            except ValueError:
               continue

         readDataLine = True
         cursor.execute(cmd + 'values(?, ?, ?, ?, ?, ?, ?)', (symbol, date, row[2], row[3], row[4], row[5], row[6]))
   
   con.commit()
   cursor.close()

def addExchangeZipFiles(exchange, filePaths):
   global config, options

   dbPath = config.get('General', 'DbPath')
   tableName = config.get(exchange, "Table")
   
   tempDir = tempfile.mkdtemp()

   for filePath in filePaths:
      if zipfile.is_zipfile(filePath):
         zipFile = zipfile.ZipFile(filePath)
         if options.verbose:
            print "Unzipping " + filePath
         zipFile.extractall(tempDir)
         zipFile.close()
      else:
         if options.verbose:
            print "\"" + filePath + "\" is not a zip file\n"
   
   if options.verbose:
      print "Sorting the file list"

   dataFiles = [os.path.join(tempDir, oo) for oo in os.listdir(tempDir)]
   dataFiles.sort()
   addExchangeFiles(exchange, dataFiles)

   if os.path.exists(tempDir):
      shutil.rmtree(tempDir)
 
def buildExchange(exchange, filePaths):
   
   """
   Re-creates the table for the specified exchange. The input files are
   expected to be zip files, each of which contains multiple csv files
   with historic data.
   
   These files are available for download on www.eoddata.com once you
   purchase "Historical Data" for a particular exchange.
   """

   global config, options

   dbPath = config.get('General', 'DbPath')
   tableName = config.get(exchange, "Table")
   
   con = sqlite3.connect(dbPath)
   cursor = con.cursor()
   
   if options.verbose:
      print "Removing table " + tableName

   cursor.execute('drop table if exists ' + tableName)
   con.commit()
   cursor.close()
   
   tempDir = tempfile.mkdtemp()

   for filePath in filePaths:
      if zipfile.is_zipfile(filePath):
         zipFile = zipfile.ZipFile(filePath)
         if options.verbose:
            print "Unzipping " + filePath
         zipFile.extractall(tempDir)
         zipFile.close()
      else:
         if options.verbose:
            print "\"" + filePath + "\" is not a zip file\n"
   
   if options.verbose:
      print "Sorting the file list"

   dataFiles = [os.path.join(tempDir, oo) for oo in os.listdir(tempDir)]
   dataFiles.sort()
   addExchangeFiles(exchange, dataFiles)

   if os.path.exists(tempDir):
      shutil.rmtree(tempDir)
   
def buildAllExchanges():
   
   """
   Re-builds all the exchanges defined in the ini file. For each exchange
   the function calls buildExchange with the proper settings from the ini
   file.
   """
   
   global config, options
   
   for item in config.items("Exchanges"):
      exchange = item[0]
      
      dir = config.get(exchange, "Dir")
      
      filePaths = []
      for filePath in os.listdir(dir):
         fullPath = os.path.join(dir, filePath)

         if zipfile.is_zipfile(fullPath):
            filePaths.append(fullPath)
            
      buildExchange(exchange, filePaths)   
      
def extractAllSymbols():
   
   """
   
   Extracts all interesting symbols defined in the ini file.
   
   """
   
   global config, options
   
   for item in config.items("Exchanges"):
      extractExchangeSymbols(item[0])

def downloadExchangeFiles(user, password, remotePath, localPath, since):
   if os.path.exists(localPath):
      shutil.rmtree(localPath)
   os.mkdir(localPath)

   ftp = ftplib.FTP("ftp.eoddata.com")
   ftp.login(user, password)

   if remotePath:
      ftp.cwd(remotePath)

   nlst = ftp.nlst()
   
   fileStarts = [config.get(oo[0], 'FileStart') for oo in config.items("Exchanges")]

   for file in nlst:
      for fileStart in fileStarts:
         if file.startswith(fileStart):
            if since:
               fileStartLen = len(fileStart)
               dateStr = file[fileStartLen:(fileStartLen+8)]
               if dateStr > since:
                  processFile = True
               else:
                  processFile = False
            else:
               processFile = True

            if processFile:
               if options.verbose:
                  print "Downloading " + file + " to " + localPath
               outfile = open(os.path.join(localPath, file), 'w')
               ftp.retrbinary("RETR " + file, outfile.write)
               outfile.close()
               break

   ftp.close()

def downloadDaily(user, password):

   """
   Downloads the daily csv files from ftp.eoddata.com and stores them locally.
   The daily files are retrieved from the root directory of the server and
   are filtered by the exchange name. For example, if the NYMEX exchange is
   in the ini, then all NYMEX_* files are downloaded from the ftp and stored
   in the directory defined in the ini file.
   """
   
   global config, options
   
   dailyPath = config.get('General', 'DailyDir')
   downloadExchangeFiles(user, password, '', dailyPath, '')

def downloadHistory(user, password, since):
   global config, options
   
   historyPath = config.get('General', 'HistoryDir')
   downloadExchangeFiles(user, password, 'History', historyPath, since)

def addDaily():
   global config, options
   
   dailyPath = config.get('General', 'DailyDir')

   exchanges = [oo[0] for oo in config.items("Exchanges")]
   
   allFiles = os.listdir(dailyPath)
   
   for exchange in exchanges:
      filePaths = []
      fileStart = config.get(exchange, 'FileStart')
      for file in allFiles:
         if file.startswith(fileStart):
            filePaths.append(os.path.join(dailyPath, file))
      addExchangeFiles(exchange, filePaths)

def addHistory():
   global config, options
   
   historyPath = config.get('General', 'HistoryDir')

   exchanges = [oo[0] for oo in config.items("Exchanges")]
   
   allFiles = os.listdir(historyPath)
   
   for exchange in exchanges:
      filePaths = []
      fileStart = config.get(exchange, 'FileStart')
      for file in allFiles:
         if file.startswith(fileStart):
            filePaths.append(os.path.join(historyPath, file))
      addExchangeFiles(exchange, filePaths)

def verifyNames(exchange, symbolsFile):
   global config, options
            
   dbPath = config.get('General', 'DbPath')
   tableName = config.get(exchange, "Table")

   symbols = set()
   with open(symbolsFile, 'r') as ff:
      while True:
         line = ff.readline()
         if not line:
            break
         parts = line.split(None, 1)
         if len(parts) > 0:
            symbols.add(parts[0].upper())

   con = sqlite3.connect(dbPath)
   cursor = con.cursor()
   
   cursor.execute('select distinct(symbol) from ' + tableName)
   for row in cursor:
      symbol = row[0]
      if symbol.upper() not in symbols:
         print symbol.upper(), ' not in the symbol list'
      
   con.commit()
   cursor.close()

def main(argv=None):
   if argv is None:
      argv = sys.argv
      
   usage = "usage: %prog [options] arguments"
   parser = optparse.OptionParser(usage)

   parser.add_option("--add", action="store_true", dest="add", help="Add files")   
   parser.add_option("--add-zip", action="store_true", dest="add_zip", help="Add zip files")   
   parser.add_option("--extract", dest="extract", help="Extract SYMBOL", metavar="SYMBOL")
   parser.add_option("--replace", action="store_true", dest="replace", help="Replace on conflict")
   parser.add_option("--verbose", action="store_true", dest="verbose", help="Verbose")
   parser.add_option("--cfg", dest="cfg", help="Config file path", default="eoddata.ini", metavar="CFGPATH")
   parser.add_option("--exchange", dest="exchange", help="Exchange to work on", metavar="EXCHANGE")
   parser.add_option("--extract-symbols", action="store_true", dest="extract_symbols", help="Extract all configured symbols")
   parser.add_option("--header", action="store_true", dest="header", help="skip header")
   parser.add_option("--user", dest="user", help="User name for the ftp connections", metavar="USER")
   parser.add_option("--password", dest="password", help="Password for the ftp connections", metavar="PASSWORD")
   parser.add_option("--download-daily", action="store_true", dest="download_daily", help="Download daily data")
   parser.add_option("--add-daily", action="store_true", dest="add_daily", help="Add the daily data to the database")
   parser.add_option("--download-history", action="store_true", dest="download_history", help="Download the short term history data")
   parser.add_option("--since", dest="since", help="Don't consider dates earlier than this")
   parser.add_option("--add-history", action="store_true", dest="add_history", help="Add the short term history data to the database")
   parser.add_option("--build-exchange", dest="build_exchange", help="Build an exchange from scratch (from zip files)", metavar="EXCHANGE")
   parser.add_option("--build-exchanges", action="store_true", dest="build_exchanges", help="Build all exchanges from scratch")
   parser.add_option("--verify-names", dest="verify_names", help="Checks whether all symbols for an exchange are as in the list", metavar="FILE")
   
   global options, args, config
   (options, args) = parser.parse_args()
   
   config = ConfigParser.ConfigParser()
   config.optionxform = str   # Makes the parser case sensitive
   config.read(options.cfg)

   if options.build_exchanges:
      buildAllExchanges()
   elif options.extract_symbols:
      extractAllSymbols()
   elif options.add_daily:
      addDaily()
   elif options.download_daily:
      password = options.password
      user = options.user
      if not password or not user:
         print "Invalid user/password combination"
      else: 
         downloadDaily(user, password)
   elif options.download_history:
      password = options.password
      user = options.user
      if not password or not user:
         print "Invalid user/password combination"
      else: 
         downloadHistory(user, password, options.since)
   elif options.add_history:
      addHistory()
   elif options.build_exchange:
      filePaths = []
      for filePattern in args:
         for filePath in glob.glob(filePattern):
            filePaths.append(filePath)
            
      buildExchange(options.build_exchange, filePaths)   
   elif options.add:
      if not options.exchange:
         print "--add requires --exchange"
      else:
         filePaths = []
         for filePattern in args:
            for filePath in glob.glob(filePattern):
               filePaths.append(filePath)
            
         addExchangeFiles(options.exchange, filePaths)
   elif options.add_zip:
      filePaths = []
      for filePattern in args:
         for filePath in glob.glob(filePattern):
            filePaths.append(filePath)
            
      addExchangeZipFiles(options.exchange, filePaths)
   elif options.extract:
      if not options.exchange:
         print "--extract requires --exchange"
      else:
         extractSymbol(options.extract, options.exchange)
   elif options.verify_names:
      if not options.exchange:
         print "--verify-names requires --exchange"
      else:
         verifyNames(options.exchange, options.verify_names)

if __name__ == "__main__":
   sys.exit(main())
