
import sys, getopt, esm_calendar

def main(args):
	sdate=args[-1]
	if "--" in args:
		args=args[:-2]	
	else:
		args=args[:-1]	
	try:
		optlist, rest = getopt.getopt(args, 'f:hms')
	except getopt.GetoptError as err:
		print str(err)  # will print something like "option -a not recognized"
        	usage()
        	sys.exit(2)
	calendar_type=1
	cal=esm_calendar.calendar(calendar_type)
	date=esm_calendar.date(sdate, cal)
	printhours = printminutes = printseconds = False
	for o,a in optlist:
		if o == "-f":
			form = int(a)
		elif o == "-h":
			printhours=True
		elif o == "-m":
			printminutes=True
		elif o == "-s":
			printseconds=True
		else:
			assert False, "unhandled option"
	date.output(form, printhours, printminutes, printseconds)

main(sys.argv[1:])	
