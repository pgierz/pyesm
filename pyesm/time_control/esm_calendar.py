
class dateformat:
	datesep=["", "-", "-", "-", " ", " ", "", "-", "", "", "/"]
	timesep=["", ":", ":", ":", " ", ":", ":", "", "", "", ":"]
	dtsep=["_", "_", "T", " ", " ", " ", "_", "_", "", "_", " "]
		

	def __init__(self, form = 1, printhours = True, printminutes = True, printseconds = True):
		self.form = form
		self.printseconds = printseconds
		self.printminutes = printminutes
		self.printhours = printhours

class calendar:

	timeunits=["years", "months", "days", "hours", "minutes", "seconds"]
	monthnames=["Jan", "Feb", "Mar", "Apr", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

	def __init__(self, calendar_type = 1):
		self.calendar_type=calendar_type

	def leapyear(self, year):
		if (self.calendar_type == 1) and ((year%4 == 0 and not year%100 == 0) or year%400 == 0): 
			leapyear=1 
		else:
			leapyear=0
		return leapyear

	def diy(self, year):
		if self.calendar_type == 0 or self.calendar_type == 1:
			diy=365+self.leapyear(year)
		else:
			diy=12*self.calendar_type
		return diy

	def dim(self, year, month):
		if self.calendar_type == 0 or self.calendar_type == 1:
			if month in [1, 3, 5, 7, 8, 10, 12]:
				dim = 31
			elif month in [4,6,9,11]:
				dim = 30
			else:
				dim=28+self.leapyear(year)
		else:
			dim=self.calendar_type
		return dim



class date:

	def __init__(self, indate, calendar):
		printhours=True
		printminutes=True
		printseconds=True
		ndate=["1900","01","01", "00", "00", "00"]
		if "T" in indate:
			indate2=indate.replace('T','_')
		else:
			indate2=indate
		if "_" in indate2:
			date,time=indate2.split("_")
		else:
			date=indate2
			time=""
			ts=":"
		for index in [3,4,5]:
			if len(time) == 2:
				ndate[index]=time
				time=time[2:]
			elif len(time) > 2:
				ndate[index]=time[:2]
				if len(time)>2:
					time=time[2:]
					if time[0]==":":
						time=time[1:]
						ts=":"
			else:
				ndate[index]="00"
				if index == 3:
					printhours=False
				elif index==4:
					printminutes=False
				elif index==5:
					printseconds=False
		for index in [2,1]:
			ndate[index]=date[-2:]
			date=date[:-2]	
			if date[-1]=="-":
				date=date[:-1]
				ds="-"
		ndate[0]=date
		if ds == "-" and ts == ":":
			if "T" not in indate:
				form=1
			else:
				form=2
		elif ds == "-" and ts == "":
			form=7
		elif ds == "" and ts == ":":
			form=6
		elif ds == "" and ts == "":
			form=9
		self.df=dateformat(form, printhours, printminutes, printseconds)
		self.date=map(int,ndate)
		self.calendar= calendar

	def __eq__(self, other):
		return( (self.date[1] == other.date[1]) and
                        (self.date[2] == other.date[2]) and
                        (self.date[3] == other.date[3]) and 
                        (self.date[4] == other.date[4]) and 
                        (self.date[5] == other.date[5]) and 
                        (self.date[0] == other.date[0]))

	def __gt__(self, other):
		return ( (self.date[0] >  other.date[0]) or  
			((self.date[0] == other.date[0]) and ((self.date[1] > other.date[1]) or
			((self.date[1] == other.date[1]) and ((self.date[2] > other.date[2]) or 
			((self.date[2] == other.date[2]) and ((self.date[3] > other.date[3]) or 
			((self.date[3] == other.date[3]) and ((self.date[4] > other.date[4]) or 
			((self.date[4] == other.date[4]) and  (self.date[5] > other.date[5])))))))))))

	def __ge__(self,other):
		return (self > other or self == other)

	def __lt__(self, other): 
		return (other > self)

	def __le__(self, other):
		return (other >= self)

	def __sub__(self, other):
		diff=[0,0,0,0,0,0]
		for i in [5,4,3,2]:
			diff[i]=diff[i] + d2[i] - d1[i]
			if diff[i] < 0:
				diff[i-1]=diff[i-1]-1
			
		while d1[1] > 1:
			diff[1]=diff[1] - 1
			d1[1] = d1[1] - 1
			diff[2] = diff[2] - self.calendar.dim(d1[0], d1[1])

		while d2[1] > 1:
			diff[1]=diff[1] + 1
			d2[1] = d2[1] - 1
			diff[2] = diff[2] + self.calendar.dim(d2[0], d2[1])

		if diff[1] < 0:
			diff[0] = diff[0] - 1

		while d1[0] < d2[0]:
			diff[0] = diff[0] + 1
			diff[1] = diff[1] + 12
			diff[2] = diff[2] + self.calendar.diy(d1[0])
			d1[0] = d1[0] + 1

		diff[3] = diff[3] + diff[2]*24
		if diff[3] < 0:
			diff[3]=diff[3] + 24	
		diff[4] = diff[4] + diff[3]*60
		if diff[4] < 0:
			diff[4]=diff[4] + 60	
		diff[5] = diff[5] + diff[4]*60
		if diff[5] < 0:
			diff[5]=diff[5] + 60	

		return diff


	def time_between(self, date, outformat = "seconds"):
		if date > self:
			diff = date - self
		else:
			diff = self - date
	
		for index in range(0, 6):
			if outformat == self.calendar.timeunits[index]:
				return diff[index]


	def day_of_year(self):
	  	date2=date(self.date[0]+"-01-01T00:00:00", self.calendar)	
		return(self.time_between(date2, "days") + 1)


	def output(self, form="SELF", ph = False, pm = False, ps = False): # basically format_date
		if form == "SELF":
			form=self.df.form
		ndate=map(str,self.date)
		if form == 0:
			if len(ndate[0]) < 4:
				for i in range(1, 4 - len(ndate[0])):
					ndate[0]="0"+ndate[0]
		elif form == 5:
			temp=ndate[0]
			ndate[0]=ndate[2]
			ndate[2]=temp
			ndate[1]=self.calendar.monthnames[int(ndate[1]) - 1]
		elif form == 8:
			if len(ndate[0]) < 4:
				print('Format 8 clear with 4 digit year only')
				sys.exit(2)
		elif form == 10:
			temp=ndate[0]
			ndate[0]=ndate[1]
			ndate[1]=ndate[2]
			ndate[2]=temp

		for index in range(0,6):
			if len(ndate[index]) < 2:
				ndate[index]="0"+ndate[index]

		ndate[1]=self.df.datesep[form]+ndate[1]
		ndate[2]=self.df.datesep[form]+ndate[2]
		ndate[3]=self.df.dtsep[form]+ndate[3]
		ndate[4]=self.df.timesep[form]+ndate[4]
		ndate[5]=self.df.timesep[form]+ndate[5]

		if not ps and not self.df.printseconds:
			ndate[5]=""	
		if not pm and not self.df.printminutes and ndate[5]=="":
			ndate[4]=""	
		if not ph and not self.df.printhours and ndate[4]=="":
			ndate[3]=""
	
		print(ndate[0] + ndate[1] + ndate[2] + ndate[3] + ndate[4] + ndate[5])


	def makesense(self):
		ndate=self.date
		ndate[4]=ndate[4] + ndate[5] / 60
		ndate[5]=ndate[5] % 60

		ndate[3]=ndate[3] + ndate[4] / 60
		ndate[4]=ndate[4] % 60

		ndate[2]=ndate[2] + ndate[3] / 24
		ndate[3]=ndate[3] % 24

		while ndate[2] > self.calendar.dim(ndate[1], ndate[0]):
			ndate[2] = ndate[2] - self.calendar.dim(ndate[1], ndate[0])
			ndate[0] = ndate[0] + ndate[1] / 12
			ndate[1] = ndate[1] % 12
			ndate[1] = ndate[1] + 1

		while ndate[2] <= 0:
			ndate[1] = ndate[1] - 1
			ndate[0] = ndate[0] + ndate[1] / 12
			ndate[1] = ndate[1] % 12
			if ndate[1] == 0:
				ndate[1] = 12
				ndate[0] = ndate[0] - 1
			ndate[2] = ndate[2] + self.calendar.dim(ndate[1], ndate[0])

		ndate[0]=ndate[0] + ndate[1] / 12
		ndate[1]=ndate[1] % 12
		if ndate[1] == 0:
			ndate[1] = 12
			ndate[0] = ndate[0] - 1
		self.date=ndate


	def add(self, to_add):
		ndate=self.date
		for index in range(0, 6):
			ndate[index]=ndate[index] + to_add[index]
		self.makesense()	

	def sub(self, to_sub):
		ndate=self.date
		for index in range(0, 6):
			ndate[index]=ndate[index] - to_sub[index]
		self.makesense()	

