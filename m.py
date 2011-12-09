#!/usr/bin/env python

"""A python email program. A slightly modifed version from

http://docs.python.org/library/email-examples.html

"""

import os
import sys
import smtplib
# For guessing MIME type based on file name extension
import mimetypes

from optparse import OptionParser

from email import encoders
from email.message import Message
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

COMMASPACE = ', '


def main():
	parser = OptionParser(usage="""\
Send email to recipient(s) with optional attachments

Usage: %prog [options]

Unless the -o option is given, the email is sent by forwarding to the SMTP server,
which is either specified through -t option or defaulted to 'localhost'. When -o is
used, generated content is written to filename specified by -o.
""")
	parser.add_option('-o', '--output',
					  type='string', action='store', metavar='FILE',
					  help="""Print the composed message to FILE instead of
					  sending the message to the SMTP server.""")
	parser.add_option('-s', '--subject',
					  type='string', action='store', metavar='SUBJECT', default='[NO SUBJECT]',
					  help='The value of the Subject: header, default to [NO SUBJECT]')
	parser.add_option('-f', '--from',
					  type='string', action='store', metavar='FROM', dest='frm',
					  help='The value of the From: header (required)')
	parser.add_option('-r', '--recipient',
					  type='string', action='append', metavar='RECIPIENT',
					  default=[], dest='recipients',
					  help='A To: header value (at least one required)')
	parser.add_option('-t', '--through',
					  type='string',  metavar='THROUGH', default='localhost',
					  help="""SMTP server ip (or hostname) that this program
					  will send mail through, defaults to localhost.""")
	parser.add_option('-a', '--attach',
					  type='string', action='append', metavar='ATTACH',
					  default=[], dest='attachments',
					  help='filename to attach, optional')
	parser.add_option('-d', '--debug',
					  action='store_true', metavar='DEBUG',
					  default=[], dest='debug',
					  help='turn on debugging')
	opts, args = parser.parse_args()
	if not opts.frm or not opts.recipients:
		parser.print_help()
		sys.exit(1)
	# Create the enclosing (outer) message
	outer = MIMEMultipart()
	outer['Subject'] = opts.subject
	outer['To'] = COMMASPACE.join(opts.recipients)
	outer['From'] = opts.frm
	outer.preamble = 'You will not see this in a MIME-aware mail reader.\n'

	for filename in opts.attachments:
		if not os.path.isfile(filename):
			continue
		# Guess the content type based on the file's extension.  Encoding
		# will be ignored, although we should check for simple things like
		# gzip'd or compressed files.
		ctype, encoding = mimetypes.guess_type(filename)
		if ctype is None or encoding is not None:
			# No guess could be made, or the file is encoded (compressed), so
			# use a generic bag-of-bits type.
			ctype = 'application/octet-stream'
		maintype, subtype = ctype.split('/', 1)
		if maintype == 'text':
			fp = open(filename)
			# Note: we should handle calculating the charset
			msg = MIMEText(fp.read(), _subtype=subtype)
			fp.close()
		elif maintype == 'image':
			fp = open(filename, 'rb')
			msg = MIMEImage(fp.read(), _subtype=subtype)
			fp.close()
		elif maintype == 'audio':
			fp = open(filename, 'rb')
			msg = MIMEAudio(fp.read(), _subtype=subtype)
			fp.close()
		else:
			fp = open(filename, 'rb')
			msg = MIMEBase(maintype, subtype)
			msg.set_payload(fp.read())
			fp.close()
			# Encode the payload using Base64
			encoders.encode_base64(msg)
		# Set the filename parameter
		msg.add_header('Content-Disposition', 'attachment', filename=filename)
		outer.attach(msg)
	# Now send or store the message
	composed = outer.as_string()
	if opts.debug:
		print "DEBUG=>", opts
	if opts.output:
		fp = open(opts.output, 'w')
		fp.write(composed)
		fp.close()
	else:
		s = smtplib.SMTP(opts.through)
		s.sendmail(opts.frm, opts.recipients, composed)
		s.quit()


if __name__ == '__main__':
	main()
