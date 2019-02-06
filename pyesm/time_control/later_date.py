#!/usr/bin/env python

import sys, getopt, esm_calendar

def main(args):
	sdate1=args[-2]
	sdate2=args[-1]
	if "--" in args:
		args=args[:-3]
	else:
		args=args[:-2]

	try:
		optlist, rest = getopt.getopt(args, 'c:')
	except getopt.GetoptError as err:
		print str(err)  # will print something like "option -a not recognized"
        	usage()
        	sys.exit(2)
	calendar_type=1
	for o,a in optlist:
		if o == "-c":
			calendar_type = int(a)
		else:
			assert False, "unhandled option"
	cal=esm_calendar.calendar(calendar_type)
	date1=esm_calendar.date(sdate1, cal)
	date2=esm_calendar.date(sdate2, cal)
	if date1 >= date2:
		date1.output()
	else:
		date2.output()

main(sys.argv[1:])	
