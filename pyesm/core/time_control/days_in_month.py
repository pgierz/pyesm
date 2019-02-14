#!/usr/bin/env python
import sys, getopt, esm_calendar

def main(args):
	year=int(args[-2])
	month=int(args[-1])
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
	print(cal.dim(year, month))

main(sys.argv[1:])	
