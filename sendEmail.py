import os, sys, smtplib, optparse
from email.mime.text import MIMEText

options = None
args = None

def main(argv=None):
   if argv is None:
      argv = sys.argv
      
   usage = "usage: %prog [options] arguments"
   parser = optparse.OptionParser(usage)

   parser.add_option("-s", "--subject", dest="subject", help="Subject")   
   parser.add_option("-f", "--from", dest="email_from", help="From")   
   parser.add_option("-t", "--to", dest="email_to", help="To")   
   parser.add_option("-c", "--content", dest="content", help="The content file")   
   parser.add_option("-p", "--password", dest="password", help="Password")   
   parser.add_option("-u", "--user", dest="user", help="User")   
   
   global options, args
   (options, args) = parser.parse_args()

   # Read the content
   ff = open(options.content, 'r')
   cc = ff.read()
   ff.close()

   msg = MIMEText(cc)
   msg['Subject'] = options.subject
   msg['From'] = options.email_from
   msg['To'] = options.email_to
   
   server = smtplib.SMTP('smtp.gmail.com', 587)
   server.ehlo()
   server.starttls()
   server.login(options.user, options.password)
   server.sendmail(options.email_from, [options.email_to], msg.as_string())
   server.quit()

if __name__ == "__main__":
   sys.exit(main())
