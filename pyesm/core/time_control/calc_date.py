#!/usr/bin/env python
import sys, getopt, esm_calendar

def main(args):
	command = args[0]
	sdate=args[-1]
	if "--" in args:
		args=args[1:-2]	
	else:
		args=args[1:-1]	
	try:
		optlist, rest = getopt.getopt(args, 'c:Y:M:D:h:m:s:')
	except getopt.GetoptError as err:
		print str(err)  # will print something like "option -a not recognized"
        	usage()
        	sys.exit(2)
	add_sub=[0,0,0,0,0,0]
	calendar_type=1
	for o,a in optlist:
		if o == "-c":
			calendar_type = int(a)
		elif o == "-Y":
			add_sub[0] = int(a)
		elif o == "-M":
			add_sub[1] = int(a)
		elif o == "-D":
			add_sub[2] = int(a)
		elif o == "-h":
			add_sub[3] = int(a)
		elif o == "-m":
			add_sub[4] = int(a)
		elif o == "-s":
			add_sub[5] = int(a)
		else:
			assert False, "unhandled option"
	cal=esm_calendar.calendar(calendar_type)
	date=esm_calendar.date(sdate, cal)
	if command == "plus":
		date.add(add_sub)	
	elif command == "minus":
		date.sub(add_sub)
	date.output()

main(sys.argv[1:])	
