#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 26 03:33:17 2020

@author: Shuai Pan
"""

from pyomo.environ import *

model = AbstractModel()
data = DataPortal()

model.acolor_name = Set(initialize=['clear', 'green', 'brown'])
model.bcolor_name = Set(initialize=['brwon', 'color', 'green', 'mixed', 'clear'])
model.area = RangeSet(1, 3)
model.facility = RangeSet(1, 2)
model.factory = RangeSet(1, 2)
model.bcolor = RangeSet(1, 5)
model.acolor = RangeSet(1, 3)
model.bids = RangeSet(1, 4)
model.piece = RangeSet(0, 4)
model.p = RangeSet(1,4)

#the amount of bcolor glass in area
model.amount = Param(model.area, model.bcolor)
model.pretran_cost = Param(model.facility, model.area, model.bcolor)
#the convert factor from bcolor to acolor. note: the convert factor of all facilities is the same
model.convert = Param(model.acolor, model.bcolor)
#the sell price of acolor glass in factory
model.sell = Param(model.factory, model.acolor)
#the pretransportation cost of bcolor glass from area to facility
model.posttrans_cost = Param(model.facility, model.factory, model.acolor)
model.bid_price = Param(model.facility, model.bids)
model.min_tons = Param(model.facility, model.piece)

model.delta = Var(model.facility, model.bids, domain=NonNegativeReals)
#the total amount of glass in facility
model.total_amount = Var(model.facility, domain=NonNegativeReals)
#the amount of bcolor glass transported from area to facility
model.x = Var(model.facility, model.area, model.bcolor, domain=NonNegativeReals)
#the amount of acolor glass transported from facility to factory
model.y = Var(model.factory, model.facility, model.acolor, domain=NonNegativeReals)
#the amount of acolor glass after convertion in facility
model.camount = Var(model.facility, model.acolor, domain=NonNegativeReals)
model.is_use = Var(model.facility, model.piece, domain=Boolean)
model.total_price = Var(domain=NonNegativeReals)

#load data
data.load(filename='pretran_cost.csv', param=model.pretran_cost, 
          index= (model.facility, model.area, model.bcolor))
data.load(filename='amount.csv', param=model.amount, format='array')
data.load(filename='convert.csv', param=model.convert, format='array')
data.load(filename='sell.csv', param=model.sell, format='array')
data.load(filename='posttrans_cost.csv', param=model.posttrans_cost,
          index = (model.facility, model.factory, model.area))
data.load(filename='min_tons.csv', param=model.min_tons, format='array')
data.load(filename='bid_price.csv', param=model.bid_price, format='array')

def ObjRule(model):
    return sum(model.y[i,j,k] * model.sell[i,k] 
                for i in model.facility for j in model.factory for k in model.acolor)\
             - sum(model.x[i,j,k] * model.pretran_cost[i,j,k] for i in model.facility
                   for j in model.area for k in model.bcolor) \
              - sum(model.y[i,j,k] * model.posttrans_cost[i,j,k] for i in model.facility
                    for j in model.factory for k in model.acolor)\
              - model.total_price
                
def con1(model, f, p):
    '''
    

    Parameters
    ----------
    model : pyomo object
        abstract model
    f : rangeSet
        range set of facility
    p : rangeSet
        range set of p

    Returns
    -------
    expression
        if the bid is choosed, then delta need to smaller than the maximum amount
        controlled by that bid.

    '''
    return model.delta[f,p] <= (model.min_tons[f,p] - model.min_tons[f, p-1]) \
        * model.is_use[f, p-1]
    
def con2(model, f, p):
    '''
    

    Parameters
    ----------
    model : pyomo object
        abstract model
    f : rangeSet
        range set of facility
    p : rangeSet
        range set of p

    Returns
    -------
    expression
        if the bid is choosed, then delta need to greater than the minimum amount
        controlled by that bid.

    '''
    return model.delta[f,p] >= (model.min_tons[f,p] - model.min_tons[f, p-1]) \
        * model.is_use[f, p]

def con3(model, f):
    '''
    

    Parameters
    ----------
    model : pyomo object
        abstract model
    f : rangeSet
        range set of facility

    Returns
    -------
    expression
        The total amount equal to the sum of all bids amount.

    '''
    return sum(model.delta[f,b] for b in model.bids) == model.total_amount[f]

def con4(model):
    '''
    

    Parameters
    ----------
    model : pyomo object
        abstract model
        
    Returns
    -------
    expression
        The total price equal to the sum of all bids price multiply amount.

    '''
    return model.total_price == sum(model.delta[i,j] * model.bid_price[i,j] 
                                    for i in model.facility for j in model.bids)

def con5(model, a, b):
    '''
    

    Parameters
    ----------
    model : pyomo object
        abstract model
    a : rangeSet
        range set of facility
    b : rangeSet
        range set of acolor

    Returns
    -------
    expression
        Calculate the amount of bcolor glass after convert in facility.

    '''
    return model.camount[a,b] == sum(model.x[a,b,c] * model.convert[d,c] for d in model.area
                                                  for c in model.bcolor)

def con6(model, a):
    '''
    

    Parameters
    ----------
    model : pyomo object
        abstract model
    a : rangeSet
        range set of facility

    Returns
    -------
    expression
        Calculate the total amount in facility.

    '''
    return model.total_amount[a] == sum(model.camount[a,b] for b in model.acolor)

def con7(model, b, c):
    '''
    

    Parameters
    ----------
    model : pyomo object
        abstract model
    b : rangeSet
        range set of area
    c : rangeSet
        range set of bcolor

    Returns
    -------
    expression
        The amount of bcolor glass collecyed in area transported to facility
        should equal  to the amount of bcolor glass in this area.

    '''
    return model.x[1,b,c] + model.x[2,b,c] == model.amount[b,c]

def con8(model, b, c):
    '''
    

    Parameters
    ----------
    model : pyomo object
        abstract model
    b : rangeSet
        range set of area
    c : rangeSet
        range set of bcolor

    Returns
    -------
    expression
        The amount of acolor glass converted in facility transported to factory
        should equal to the amount of acolor glass produced in this facility.

    '''
    return model.y[1,b,c] + model.y[2,b,c] <= model.camount[b,c]


#objective function
model.profit = Objective(rule=ObjRule, sense=maximize)

#constraint
model.con1 = Constraint(model.facility, model.p, rule=con1)
model.con2 = Constraint(model.facility, model.p, rule=con2)
model.con3 = Constraint(model.facility, rule=con3)
model.con4 = Constraint(rule=con4)
model.con5 = Constraint(model.facility, model.acolor, rule=con5)
model.con6 = Constraint(model.facility, rule=con6)
model.con7 = Constraint(model.area, model.bcolor, rule=con7)
model.con8 = Constraint(model.facility, model.acolor, rule=con8)
     
instance = model.create_instance(data)
results = SolverFactory('glpk').solve(instance, tee=True)
results.write()

                

