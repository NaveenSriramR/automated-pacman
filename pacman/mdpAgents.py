# Name: Naveen Sriram Ramkumar
# ID: K23058773
from pacman import Directions
from game import Agent
import api
import random
import game
import util


class MDPAgent(Agent):
    def __init__(self):
        self.once=False
        self.FOOD_VALUE=40
        self.epsilon=0.1
        self.EMPTY_VALUE = 1
        self.WALL_VALUE = None

    def getAction(self, state):
        legal = api.legalActions(state)
        pos = api.whereAmI(state)

        if not self.once:
            # Creates initial map structure with walls and empty spaces
            self.mapper(state)
            self.once= True

        utils = self.map_struct.copy()
        reward = -0.4
        discount = 0.9 #gamma

        # Setting food values based on game progression
        foods= api.food(state)
        if len(foods)<10:
            self.FOOD_VALUE=500 
            self.epsilon=0.05
        elif len(foods)<20:
            self.FOOD_VALUE=100 
        elif len(foods)<40:
            self.FOOD_VALUE=50

        # adding food to utility map
        for f in foods:
            utils[f]=self.FOOD_VALUE

        # positional changes for utility calculation and ghost protection
        dirs=[[(0,1),(-1,0),(1,0)], # up #(col,row)
        [(-1,0),(0,1),(0,-1)], #left
        [(1,0),(0,1),(0,-1)],  # right
        [(0,-1),(-1,0),(1,0)]]  #down

        # -------------------------------------------
        # Adds ghosts values to map
        # 
        # Adds negative values for legal spaces 2 units away from the ghost
        # as long as they are not blocked a way
        ghosts=api.ghostStatesWithTimes(state)
        CAPSULE_VALUE=100      
        for c,r,k in map(lambda y:(int(y[0][0]),int(y[0][1]),y[1]),ghosts):
            
            # sets ghost_value based on scared or normal state
            GHOST_VALUE= -70 if k<3 else 50
            utils[(c,r)]=GHOST_VALUE
            if k<3:  # where k is the ghost timer

                # assigns GHOST_VALUE for all legal spaces in a 2 unit radius
                #  from ghost not blocked by a wall
                for dir in dirs:
                    i,j = dir[0]
                    # checks if first layer is wall before proceeding
                    if utils[(c+i,r+j)]!=None:
                        utils[(c+i,r+j)]=-60

                        for ii,jj in dir:
                            # checks if second layer is wall or outside map
                            if utils.get((c+i+ii,r+j+jj),None)!=None:
                                utils[(c+i+ii,r+j+jj)]= -50
                     
            else:
                # changes capsule value even if one ghost is in scared state
                discount=0.8
                CAPSULE_VALUE=-50  

        # capsule values , CAPSULE_VALUE set in ghost stage
        caps=api.capsules(state)
        for k in caps:
            # print k
            utils[k]=CAPSULE_VALUE

        # ----------------------------------------------------        
        # Value iteration step
        new_utils = utils.copy()
        # utility calculation 
        for _ in range(30):
            for c in range(1,self.width-1):
                for r in range(1,self.height-1):
                    # checks if state is ghost, capsule or food before calculating utility value
                    if utils[(c,r)]!= None and utils[(c,r)]>-50 and utils[(c,r)]<50:
                        utility=[]
                        # calculating action of highest utility using BELLMAN
                        for i in dirs:  
                            y=0.8*(utils[(c+i[0][0],r+i[0][1])] if utils[(c+i[0][0],r+i[0][1])]!=None else utils[(c,r)])
                            y+=0.1*(utils[(c+i[1][0],r+i[1][1])] if utils[(c+i[1][0],r+i[1][1])]!=None else utils[(c,r)])
                            y+=0.1*(utils[(c+i[2][0],r+i[2][1])] if utils[(c+i[2][0],r+i[2][1])]!=None else utils[(c,r)])
                            utility.append(y)
                        
                        new_utils[(c,r)]=reward + discount*max(utility)

                    else:
                        new_utils[(c,r)]=utils[(c,r)]
            
            # convergence check
            diff=[]
            for key in new_utils.keys():
                if utils[key]!=None:
                    diff.append(utils[key]-new_utils[key])
            utils=new_utils.copy()
            if max(diff)<=self.epsilon:
                break

        # ----------------------------------------------------
        # Processing next move 
        move_map={
            'North':(0,1),
            'South':(0,-1),
            'West':(-1,0),
            'East':(1,0)
            }
        if Directions.STOP in legal:
                    legal.remove(Directions.STOP)        
        move=float('-inf')
        # finding move with highest utility
        for a in legal:
            b=move_map[a]
            if utils[(pos[0]+b[0],pos[1]+b[1])]>move:
                move = utils[(pos[0]+b[0],pos[1]+b[1])]
                dir=a
        
        return api.makeMove(dir, legal)

    # Creates the base map structure containing the walls and legal spaces.
    # This map is used in future getAction() calls with the food, ghost and capsule values added
    def mapper(self,state):
        corners = api.corners(state) 
        fin={}
        self.width = corners[-1][0]+1
        self.height = corners[-1][1]+1

        # Creates a map of nescessary size with all values as empty
        for c in range(self.width):
            for r in range(self.height):
                fin[(c,r)]=self.EMPTY_VALUE

        # adds wall values to the map
        for f in api.walls(state):
            fin[f]=self.WALL_VALUE

        #stores map structure to be used in future getAction calls
        self.map_struct=fin.copy()
