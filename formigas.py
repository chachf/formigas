#!/bin/python
#
# A program which simulates the evolution of a group of ants in a forest. 
# S. Friedli
# Belo Horizonte, June 1st 2013

from Tkinter import *
from random import *
from time import *
from math import tanh


# Maximal horizontal size on my ASUS: 1270
# Maximal vertical size on my ASUS: 500?
# Maximal horizontal size at ICEx: 1665
# Maximal vertical size at ICEx: 980 (but 400 is more convenient)
width_canvas=1000
height_canvas=700

xzero=5
yzero=5
scale_x=10
scale_y=10

MAX_PHEROM=15

def varphi(x,eps):
	eps_1=0.4
	# plus eps est grand plus c'est sensible aux grand pics, plus eps est
#	petit plus les fourmis returning diffusent. eps=0 correspond en principe a des
#	marches aleatoires libres.
	beta=20 # Beta grand ten a liberer les particules (je sais pas pourquoi)
	return eps_1+eps*tanh(beta*x)

def trun(x): #pra usar nas cores
	return min(abs(x),255)

def Bernoulli(p):
	if random() < p:
		return 1
	else:
		return 0

def rand_choice(L,Q):
	"""Given a list of objects L=(o_1,...,o_n) with weights Q=(q_1,...,q_n), this function
	samples one of the objects o_k with probability p_k=q_k/(q_1+...+q_n). Small problem:
	if all the q_ks ar zero..."""
	P=[float(q)/sum(Q) for q in Q]
	V=[0]
	for i in range(len(L)):
		V.append(V[i]+P[i])
	p=random()
	for k in range(len(L)+1):
		if V[k]<= p <V[k+1]:
			my_choice=L[k]
	return my_choice

def step_in_direction(x,y,d):
	if d=='N':
		y=y+1
	if d=='E':
		x=x+1
	if d=='S':
		y=y-1
	if d=='W':
		x=x-1
	return x,y

class forest: # the forest
	"""A forest is a grid NxN each site of which can be in
	two states s (0=plain, 1=obstacle), with probability
	alpha. If the state is 1
	then there can be nothing there (neither ants nor
	food), if the state is 0 then ants can visit the
	site, and a certain amount of food can be there."""
	def __init__(self,canv,N,alpha_obstacle,alpha_pherom):
		self.canvas=canv
		self.linear_size=N
		self.prob_of_obstacle=alpha_obstacle
		self.prob_of_pheromone=alpha_pherom
		# We initialize the forest by setting, on each site: 
	        # the presence or absence of an obstacle [0]
		# the quantity of pheromone_A [1]
		# the quantity of food [2]
		self.grid=[[[0,0,0,0] for i in range(self.linear_size)] for j in range(self.linear_size)]
		epsilon=0.3

		### CREATE THE OBSTACLES: ############
		# To create a homogeneous Bernoulli environment:
#		for i in range(self.linear_size):
#			for j in range(self.linear_size):
#				self.grid[i][j][0]=Bernoulli(self.prob_of_obstacle)
		# To create a homogeneous Bernoulli environment made of random sticks:
#		for i in range(self.linear_size):
#			for j in range(self.linear_size):
#				if Bernoulli(self.prob_of_obstacle):
#					for l in range(randrange(25)):
#						self.grid[i][min(abs(j+l),self.linear_size-1)][0]=1
		# To create a deterministic square obstacle in the middle of the box:
		for i in range(int(self.linear_size*epsilon),int(self.linear_size*(1-epsilon))):
			for j in range(int(self.linear_size*epsilon),int(self.linear_size*(1-epsilon))):
				self.grid[i][j][0]=Bernoulli(self.prob_of_obstacle)
	
		###### CREATE INITIAL PHEROMONES: ######
#		for i in range(int(self.linear_size*epsilon),int(self.linear_size*(1-epsilon))):
#			for j in range(int(self.linear_size*0.49),int(self.linear_size*0.55)):
#				self.grid[i][j][1]=1
#				self.grid[i][j][1]=randrange(2,4)

		###### CREATE INITIAL FOOD: ######
#		for j in range(int(self.linear_size*0.49),int(self.linear_size*0.55)):
#				self.grid[2][j][2]=1
#				self.grid[i][j][1]=randrange(2,4)

		###### CREATE PHEROMONE A DICTIONARY: ###########
		self.pheromone_A={}
		for i in range(self.linear_size):
			for j in range(self.linear_size):
				if self.grid[i][j][1]>0:
					n=trun(255-self.grid[i][j][1])
					new_color = "#%02x%02x%02x" % (n,n,n) 
					self.pheromone_A[(i,j)]=[self.grid[i][j][1],
					self.canvas.create_rectangle(self.canvas.coord(i,j),
					self.canvas.coord(i+1,j+1),
					fill=new_color, width=0, tags=("pheromrect"))]

#			self.pheromone_A[(x,y)]=[quant,self.canvas.create_rectangle(self.canvas.coord(x,y),
#			self.canvas.coord(x+1,y+1), fill=new_color, width=0, tags=("pheromrect"))]
	def pure_neighbors(self,x,y):
		"""To each point of the grid we must associate the allowed
		directions (independently of the environment). The points at the
		center of the grid have 4 allowed directions, those on the boundary
		have either 2 or 3."""
		p_neighb=['N','E','S','W']
		if x==0:
			if y==0:
				p_neighb=['N','E']
			elif y==self.linear_size-1:
				p_neighb=['S','E']
			elif 0<y<self.linear_size-1:
				p_neighb=['N','E','S']
		if x==self.linear_size-1:
			if y==0:
				p_neighb=['N','W']
			elif y==self.linear_size-1:
				p_neighb=['S','W']
			elif 0<y<self.linear_size-1:
				p_neighb=['N','W','S']
		if 0<x<self.linear_size-1:
			if y==0:
				p_neighb=['W','N','E']
			if y==self.linear_size-1:
				p_neighb=['E','S','W']
		return p_neighb

	def true_neighbors(self,x,y):
		"""Determine the allowed directions from a point (x,y), depending on
		the neighboring environment"""
		t_neighb=self.pure_neighbors(x,y)
		for d in t_neighb:
			u,v=step_in_direction(x,y,d)
			if self.grid[u][v][0]>0:
				t_neighb.remove(d)
		return t_neighb	

	def add_pheromone(self,x,y,quant):
		"""Add pheromone at site (x,y), the amount of pheromone_A is limited by
		MAX_PHEROM. When the
		site does not yet contain pheromone_A, create also the associated rectangle for
		the canvas."""
		if (x,y) in self.pheromone_A:
			self.pheromone_A[(x,y)][0]=min(self.pheromone_A[(x,y)][0]+quant,MAX_PHEROM)
			n=trun(255-self.pheromone_A[(x,y)][0])
			new_color = "#%02x%02x%02x" % (n,n,n) 
			self.canvas.itemconfig(self.pheromone_A[(x,y)][1],fill=new_color)
		else:
			n=trun(255-quant)
			new_color = "#%02x%02x%02x" % (n,n,n) 
			self.pheromone_A[(x,y)]=[quant,self.canvas.create_rectangle(self.canvas.coord(x,y),
			self.canvas.coord(x+1,y+1), fill=new_color, width=0, tags=("pheromrect"))]

	def evaporate_pheromone_A(self, decr_pherom):
		# We decrease the amount of pheromone_A on each site:
		for (x,y) in list(self.pheromone_A):
			self.pheromone_A[(x,y)][0]=max(self.pheromone_A[(x,y)][0]-decr_pherom,0)
			n=trun(255-self.pheromone_A[(x,y)][0])
			new_color = "#%02x%02x%02x" % (n,n,n) 
			self.canvas.itemconfig(self.pheromone_A[(x,y)][1],fill=new_color)
			# Then, if the quantity of pheromone_A on a site became negative, we
			# delete the associated rectangle and delete the site from the
			# dictionary (the list(...) above is necessary since we are looping over a
			# dictionary from which we are removing elements):
			if self.pheromone_A[(x,y)][0]==0:
				self.canvas.delete(self.pheromone_A[(x,y)][1])
				del self.pheromone_A[(x,y)]

			
class ant:
	"""An ant is defined 
	by a type t (which represents her hierarchy: 0=queen, 1=worker,
	2= fighter etc), a status s (s='hunting' or 'returning')a position (x,y), a load l (l=0:free,
	l=m>0:loaded with m units of food), an activity a (either 1 or 0 depending on the ant being carrying
	food or not) and a color c."""

	def __init__(self,canv,t,s,x,y,l,a,c):
		self.canvas=canv
		self.hierarchy=t 
		self.status=s
		self.pos_x=x
		self.pos_y=y
		self.load=l
		self.activity=a
		self.color=c
		self.rect=self.canvas.create_oval(self.canvas.coord(self.pos_x,self.pos_y),self.canvas.coord(self.pos_x+1,self.pos_y+1),fill=self.color, width=0, tags=("antrect"))	


	def move(self,F,incr_pherom_returning, incr_pherom_hunting):
		"""The move of an ant is made according to her actual position
		and to the
		state of the forest F in which she evolves (for the time being,
		the ant doesn't consider the position of the
		other ants). When he status is "returning" (to the anthill) 
		state, she also leaves incr_pherom units of pheromone_A."""
		# When an ant is active, it drops some pheromone_A at its location (this should
		# be done BEFORE moving to a nearest neighbor):
		if self.status=='returning':
			F.add_pheromone(self.pos_x,self.pos_y,incr_pherom_returning)
		elif self.status=='hunting':
			F.add_pheromone(self.pos_x,self.pos_y,incr_pherom_hunting)
		# First, remember the actual position:
		cx,cy=self.canvas.coord(self.pos_x,self.pos_y)
		# Then, compute the authorized directions in F seen from
		# the position of the ant:
		authorized_directions=F.true_neighbors(self.pos_x,self.pos_y)
		# Look at the quantitires of pheromone_A in authorized directions:
#		neighboring_pheromone_A=[F.grid[x][y][1] for x,y in authorized_directions]
		neighboring_pheromone_A_weight=[]
		for d in authorized_directions:
			v_x,v_y=step_in_direction(self.pos_x,self.pos_y,d)
			# The "+0.1" is so that the ant always has a positive probability of
			# stepping towards a point that has no pheromone_A on it:
			if (v_x,v_y) in F.pheromone_A:
				neighboring_pheromone_A_weight.append(F.pheromone_A[(v_x,v_y)][1]**2)
			else:
				neighboring_pheromone_A_weight.append(0.01)
		# We normalize the weights using varphi: if the ant is hunting then its
		# tendency to go towards sites with pheromone_A is larger. If it's returning it
		# concentrates mainly on putting down pheromone_A
		if self.status=='hunting':
			WEIGHTS=[varphi(l,8) for l in neighboring_pheromone_A_weight]
		elif self.status=='returning':
			WEIGHTS=[varphi(l,0.1) for l in neighboring_pheromone_A_weight]
		# Then, choose randomly one of those directions, weighted by the amounts of
		# pheromone_A:
		chosen_direction=rand_choice(authorized_directions,WEIGHTS)
		# ... and make a step in that direction:
		self.pos_x,self.pos_y=step_in_direction(self.pos_x,self.pos_y,chosen_direction)
#		a.move(F)
		ax,ay=self.canvas.coord(self.pos_x,self.pos_y)
		dx=ax-cx
		dy=ay-cy
		self.canvas.move(self.rect,dx,dy)
		# First attempt at changing the status of an ant when reaching a certain
		# region of the forest:
		if (self.pos_x>0.8*F.linear_size and self.pos_y>0.8*F.linear_size and self.status=='hunting'):
			self.status='returning'
			self.canvas.itemconfig(self.rect,fill="red")
		if (self.pos_x<0.7*F.linear_size and self.pos_y<0.2*F.linear_size and self.status=='returning'):
#	sheet.create_rectangle(sheet.coord(int(0.9*N)-0.5,int(0.5*N)-0.5),sheet.coord(N+0.5,N+0.5),fill="brown")
			self.status='hunting'
			self.canvas.itemconfig(self.rect,fill="blue")

class Feuille(Canvas):

	def coord(self,a,b): #going from grid (forest) to pixel (canvas) coordinates:
		x=xzero+a*scale_x
		y=-yzero+height_canvas-b*scale_y
		return x,y

def main():
	# Initialize Main WINDOW:
	root=Tk()
	root.title("Ants")
	S="%sx%s" % (width_canvas+100,height_canvas+100)
	root.geometry(S)

	frame_canvas = Frame(root)
	frame_canvas.pack(side=TOP)

	sheet=Feuille(frame_canvas, width=width_canvas, height=height_canvas, bg="white")
	sheet.pack(side=TOP, expand=TRUE, fill=BOTH)

	do_blink = False

	def start_blinking():
		do_blink = True
		blink()

	def stop_blinking():
		do_blink = False

	start_button = Button(root, text="Run", command=start_blinking)
	stop_button = Button(root, text="Stop", command=stop_blinking)
	stop_button.pack(side=BOTTOM)
	start_button.pack(side=BOTTOM)

#	sheet.create_rectangle(5,5,width_canvas-5,height_canvas-5)

	def drawunitrec(x,y,c):
		sheet.create_rectangle(sheet.coord(x,y),sheet.coord(x+1,y+1),
		fill=c, width=0)	

	# PARAM
	N=20
	num_formigas=20
	incr_pherom_returning=1 # the amount of pheromone_A left by an ant at a location
	incr_pherom_hunting=0.01 # the amount of pheromone_A left by an ant at a location
	decr_pherom=0.0005 # the amount of pheromone_A that evaporates at each time
	time_lapse=1
	FOREST=forest(sheet,N,1,1)

	# Draw the main box:
	sheet.create_rectangle(sheet.coord(-0.5,-0.5),sheet.coord(N+0.5,N+0.5),fill="white")
	sheet.create_text(sheet.coord(N+1,N),text="N="+str(N), anchor=W)
#	sheet.create_line(sheet.coord(0,0),sheet.coord(0,N))

	# Draw the food strip:
	sheet.create_rectangle(sheet.coord(int(0.8*N)-0.5,int(0.8*N)-0.5),sheet.coord(N+0.5,N+0.5),fill="brown")

	cor0 = "#%02x%02x%02x" % (0,0,0) # black
#	for (x,y) in FOREST.pheromone_A:
#		if FOREST.pheromone_A[(x,y)][0]>0:
#			drawunitrec(x,y,cor0)

	sheet.lift("pheromrect")
	# We show the obstacles of the forest:
	for i in range(N):
		for j in range(N):
			if (FOREST.grid[i][j][0]> 0):
				 drawunitrec(i,j,cor0)

	### CREATE THE ANTS: ################
#	cor_formigas= "#%02x%02x%02x" % (0,0,255) # blue
	ANTS=[]
	for i in range(num_formigas):
#		cor_formiga= "#%02x%02x%02x" % (0, randrange(100),randrange(200)) # blue
#		if i==1:
#			# We first create the hunting ones
#			cor_formiga= "#%02x%02x%02x" % (randrange(105,130),
#			randrange(100,110),randrange(230,250)) # purplish
#			ANTS.append(ant(sheet,1,'hunting',randrange(int(0.1*N),int(0.9*N)),randrange(int(0.1*N),int(0.9*N)),0,0,cor_formiga))
#		else:
			cor_formiga= "#%02x%02x%02x" % (0,0,0)
#			(randrange(200,255), randrange(50,60),randrange(50,60)) # reddish
			ANTS.append(ant(sheet,1,'hunting',randrange(0,int(0.2*N)),
			randrange(0,int(0.2*N)),0,0,cor_formiga))

	def blink():
		# Move each ant:
		for i in range(num_formigas):
			ANTS[i].move(FOREST, incr_pherom_returning,incr_pherom_hunting)
		# Evaporate a little bit of pheromone_A on each site:
		FOREST.evaporate_pheromone_A(decr_pherom)
		# Put the rectangles that represent ants on top (otherwise they are hidden
		# behind the rectangles of the pheromone_A):
		sheet.lift("antrect")
		root.after(time_lapse,blink)

	mainloop()

if __name__ == "__main__":
	main()
