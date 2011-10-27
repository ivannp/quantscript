aggregateReturns = function( ss, leverage=1 )
{
   return( tail( cumprod( 1 + ss*leverage ), 1 ) )
}

applyIndicator = function( ss, ind )
{
   ss[head( index( ss), 1 )] = 0
   df = merge( ss, ind, all=FALSE )
   ss = as.xts( df[,1] * coredata( df[,2] ) )
   return( ss )
}

summarizeDailyReturns = function(
      ss,
      indicator,
      returns="closeToClose",
      period="annually",
      leverage=1,
      stopLoss )
{
   stopifnot( is.xts( ss ) )
   stopifnot( is.xts( indicator ) )

   if( missing( stopLoss ) )
   {
      if( tolower( returns ) == "tradeonopen" )
      {
         stopifnot( has.Op( ss ) && has.Cl( ss ) )

         # First filter out the common dates
         mm = merge( indicator, Op( ss ), Cl( ss ), na.trim( lag( Cl( ss ) ) ), all=FALSE )

         ind = as.vector( mm[,1] )
         op = as.vector( mm[,2] )
         cl = as.vector( mm[,3] )
         prevClose = as.vector( mm[,4] )

         len = length( op )
         if( len < 2 ) return( NULL )

         rr = rep( NA, len )

         prevInd = 0

         for( ii in 2:len )
         {
            if( sign( prevInd ) != sign( ind[ii] ) )
            {
               r1 = op[ii] / prevClose[ii] - 1
               r2 = cl[ii] / op[ii] - 1

               rr[ii] = ( prevInd * r1 + ind[ii] * r2 + prevInd * r1 * ind[ii] * r2 )*ind[ii]
            }
            else
            {
               # No change in position, use close to close
               rr[ii] = ( cl[ii] / prevClose[ii] - 1 )*ind[ii]
            }

            prevInd = ind[ii]
         }

         rets = na.trim( xts( rr, order.by=index( mm ) ) )
      }
      else if( tolower( returns ) == "opentoclose" )
      {
         stopifnot( has.Op( ss ) && has.Cl( ss ) )
         rets = Cl( ss ) / Op( ss ) - 1
         rets = applyIndicator( as.xts( rets ), indicator )
      }
      else if( tolower( returns ) == "betteropentoclose" )
      {
         stopifnot( has.Op( ss ) && has.Cl( ss ) )

         # First filter out the common dates
         mm = merge( indicator, Op( ss ), Cl( ss ), lag( Cl( ss ) ), all=FALSE )

         ind = as.vector( mm[,1] )
         op = as.vector( mm[,2] )
         cl = as.vector( mm[,3] )
         prevClose = as.vector( mm[,4] )

         len = length( op )
         if( len < 2 ) return( NULL )

         rr = rep( 0, len )

         for( ii in 2:len )
         {
            if( ind[ii] == 1 )
            {
               # Long only if the open is lower than the previous close
               if( op[ii] < prevClose[ii] )
               {
                  rr[ii] = cl[ii] / op[ii] - 1
               }
            }
            else if( ind[ii] == -1 )
            {
               # Short only if the open is higher than the previous close
               if( op[ii] > prevClose[ii] )
               {
                  rr[ii] = 1 - cl[ii] / op[ii]
               }
            }
         }

         rets = xts( rr, order.by=index( mm ) )
      }
      else if( tolower( returns ) == "worseopentoclose" )
      {
         stopifnot( has.Op( ss ) && has.Cl( ss ) )

         # First filter out the common dates
         mm = merge( indicator, Op( ss ), Cl( ss ), lag( Cl( ss ) ), all=FALSE )

         ind = as.vector( mm[,1] )
         op = as.vector( mm[,2] )
         cl = as.vector( mm[,3] )
         prevClose = as.vector( mm[,4] )

         len = length( op )
         if( len < 2 ) return( NULL )

         rr = rep( 0, len )

         for( ii in 2:len )
         {
            if( ind[ii] == 1 )
            {
               # Long only if the open is higher than the previous close
               if( op[ii] > prevClose[ii] )
               {
                  rr[ii] = cl[ii] / op[ii] - 1
               }
            }
            else if( ind[ii] == -1 )
            {
               # Short only if the open is lower than the previous close
               if( op[ii] < prevClose[ii] )
               {
                  rr[ii] = 1 - cl[ii] / op[ii]
               }
            }
         }

         rets = xts( rr, order.by=index( mm ) )
      }

      else
      {
         stopifnot( has.Ad( ss ) || has.Cl( ss ) )
         if( has.Ad( ss ) )
         {
            rets = Ad( ss ) / lag( Ad( ss ) ) - 1
         }
         else
         {
            rets = Cl( ss ) / lag( Cl( ss ) ) - 1
         }

         rets = applyIndicator( as.xts( rets ), indicator )
      }
   }
   else
   {
      stopifnot( stopLoss > 0 )
      stopifnot( tolower( returns ) == "closetoclose" )

      negStopLoss = -stopLoss

      op = Op( ss )
      hi = Hi( ss )
      lo = Lo( ss )
      cl = Cl( ss )

      ccRets = applyIndicator( as.xts( cl / lag( cl ) - 1 ), indicator )
      lcRets = applyIndicator( as.xts( lo / lag( cl ) - 1 ), indicator )
      hcRets = applyIndicator( as.xts( hi / lag( cl ) - 1 ), indicator )
      ocRets = applyIndicator( as.xts( op / lag( cl ) - 1 ), indicator )

      rets = ccRets

      for( ii in index( ccRets ) )
      {
         dd = as.Date( ii )

         indVal = as.numeric( coredata( indicator[dd] ) )

         if( indVal < 0 )
         {
            if( ocRets[dd] > stopLoss )
            {
               rets[dd] = -ocRets[dd]
            }
            else if( hcRets[dd] > stopLoss )
            {
               rets[dd] = negStopLoss
            }
         }
         else
         {
            if( ocRets[dd] < negStopLoss )
            {
               rets[dd] = ocRets[dd]
            }
            else if( lcRets[dd] < negStopLoss )
            {
               rets[dd] = negStopLoss
            }
         }
      }
   }

   if( tolower( period ) == "annually" )
   {
      yy = as.numeric( format( index( rets ), "%Y" ) )
      rets = aggregate( rets, yy, aggregateReturns, leverage )
   }
   else if( tolower( period ) == "quarterly" )
   {
      rets = aggregate( rets, as.yearqtr, aggregateReturns, leverage )
   }
   else if( tolower( period ) == "monthly" )
   {
      rets = aggregate( rets, as.yearmon, aggregateReturns, leverage )
   }

   return( round( rets, 4 ) )
}
