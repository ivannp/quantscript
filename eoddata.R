eoddataLoad = function( dbName, exchange, symbol )
{
   require( RSQLite )

   drv = dbDriver( "SQLite" )
   conn = dbConnect( drv, dbname=dbName )

   symbol = toupper( symbol )

   qq = dbSendQuery( conn,
                     paste( sep="",
                            "select timestamp, open, high, low, close, volume from ",
                            exchange,
                            " where symbol = '",
                            symbol,
                            "' order by timestamp asc" ) )

   df = fetch( qq, -1 )

   dbClearResult( qq )
   dbCommit( conn )
   dbDisconnect( conn )

   xx = merge( xts( df$open, order.by=as.Date( df$timestamp ) ), df$high, df$low, df$close, df$volume )
   colnames( xx ) = c( "Open", "High", "Low", "Close", "Volume" )
   return( xx )
}

eoddataLoadCsv = function(path)
{
   zz = read.zoo(path, header=F, sep=",", col.names=c("Date", "Open", "High", "Low", "Close", "Volume"))
   zz = merge(zz, zz$Close)
   colnames(zz) = c("Open", "High", "Low", "Close", "Volume", "Adjusted")
   return(as.xts(zz))
}

findMissingDates = function( zz )
{
   require( quantmod )
   require( fCalendar )

   zzi = index( zz )

   # Get the holidays between the years of the first and last date
   firstYear = as.numeric( format( first( zzi ), "%Y" ) )
   lastYear = as.numeric( format( last( zzi ), "%Y" ) )

   holidays = holidayNYSE( firstYear:lastYear )

   # Compute all business days between the first and the last date
   allDays = seq.Date( from=first( zzi ), to=last( zzi ), by=1 )
   allBizDays = allDays[isBizday( timeDate( allDays ), holidays )]

   # Match the business days against the index of the input
   missing = allBizDays[is.na( match( allBizDays, zzi ) )]

   if( length( missing ) == 0 )
   {
      return( NULL )
   }

   return( missing )
}

test.findMissingDates = function( )
{
   require( RUnit )

   allDates = seq.Date( from=as.Date( "2008-01-01" ), to=as.Date( "2011-01-01" ), by=1 )
   zz = xts( seq( 1, length( allDates ) ), order.by=allDates )
   checkEquals( findMissingDates( zz ), NULL )

   allHolidays = holidayNYSE( 2008:2011 )
   allBizDates = allDates[isBizday( timeDate( allDates ), allHolidays )]
   zz = xts( seq( 1, length( allBizDates ) ), order.by=allBizDates )
   checkEquals( findMissingDates( zz ), NULL )

   # Remove a few dates
   someDates = allBizDates[allBizDates != "2010-05-03"]
   someDates = someDates[someDates != "2010-05-04"]
   someDates = someDates[someDates != "2009-09-28"]
   zz = xts( seq( 1, length( someDates ) ), order.by=someDates)
   res = findMissingDates( zz )
   checkEquals( res, as.Date( c( "2009-09-28", "2010-05-03", "2010-05-04" ) ) )
}
