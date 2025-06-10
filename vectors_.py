from math import atan, degrees, sqrt, radians, sin, cos, pi, tan
class Vector(list):
    def __init__(self,*x, mag = None, theta=None,phi=None, deg=True, n=3):
        self.n = n
        if x:
            super().__init__(x)
        elif mag!=None and theta!=None and phi!=None:
            if deg:
                super().__init__([mag*sin(radians(phi))*cos(radians(theta)), #x-component
                                  mag*sin(radians(phi))*sin(radians(theta)),#y-component
                                  mag*cos(radians(phi))#z-component
                                  ]) 
            else:
                super().__init__([mag*sin(radians(phi))*cos(radians(theta)), #x-component
                                  mag*sin(radians(phi))*sin(radians(theta)),#y-component
                                  mag*cos(radians(phi))#z-component
                                  ]) 
        elif mag !=None and theta!=None:
            
            if deg:    
                super().__init__([mag*cos(radians(theta)), #x-component
                                  mag*sin(radians(theta))]) #y-component
                
            else:
                super().__init__([mag*cos(theta), #x-component
                                  mag*sin(theta)]) #y-component
    def mag(self):
        ans = 0
        for i in self:
            ans+=i**2
        return round(sqrt(ans),self.n)
    def ang(self,deg=True):
        if len(self)==2:
            x = self[0]
            y = self[1]
            if deg:
                if x != 0:
                    q1 = degrees(atan(y/x))
                    if x > 0 and y>0:
                        return q1
                    elif x>0 and y<0:
                        return q1+360
                    elif x < 0 and y <0:
                        return q1+180
                    elif x< 0 and y >0:
                        return q1+90
                elif x==0 and y >0:
                    return 90
                elif x==0 and y <0:
                    return 270
            else:
                if x != 0:
                    q1 = atan(y/x)
                    if x > 0 and y>0:
                        return q1
                    elif x>0 and y<0:
                        return q1+2*pi
                    elif x < 0 and y <0:
                        return q1+pi
                    elif x< 0 and y >0:
                        return q1+pi/2.0
                elif x==0 and y >0:
                    return pi/2.0
                elif x==0 and y <0:
                    return 3*pi/2.0        
    def dir(self,type='deg'):
        if type == 'deg':
            return(degrees(atan(self[1]/self[0])))

    def __add__(self,x):
        ans = []
        if len(self) == len(x):
            for idx in range(len(self)):
                ans.append(self[idx]+x[idx])
            return Vector(*ans)
        else:
            raise BaseException('Size Mismatch')
    def __radd__(self,x):
        ans = []
        if len(self) == len(x):
            for idx in range(len(self)):
                ans.append(self[idx]+x[idx])
            return Vector(*ans)
        else:
            raise BaseException('Size Mismatch')
        
    def __sub__(self,x):
        ans = []
        if len(self) == len(x):
            for idx in range(len(self)):
                ans.append(self[idx]-x[idx])
            return Vector(*ans)
        else:
            raise BaseException('Size Mismatch')
    def __rsub__(self,x):
        ans = []
        if len(self) == len(x):
            for idx in range(len(self)):
                ans.append(-self[idx]+x[idx])
            return Vector(*ans)
        else:
            raise BaseException('Size Mismatch')
    
    def __mul__(self,x):
        ans = []
        if isinstance(x,Vector) or isinstance(x,list):
            if len(self) == len(x):
                for idx in range(len(self)):
                    ans.append(self[idx]*x[idx])

                return round(sum(ans),self.n)
        elif isinstance(x,int) or isinstance(x,float):
            for idx in range(len(self)):
                ans.append(self[idx]*x)
            return Vector(*ans)
        
        else:
            raise BaseException('Size Mismatch')
    def __rmul__(self,x):
        return self.__mul__(x)
    
    def get_var_name(self):
        """Tries to find the variable name that references this object."""
        
        for var_name in globals():
            if globals()[var_name] is self:
                return var_name
        for var_name in locals():
            if locals()[var_name] is self:
                return var_name
            
        return "Vector"
    
    def __neg__(self):
        return Vector(*[-x for x in self])

    def __repr__(self):

        ans = f'{self.get_var_name()}:\t['
        for i in self:
            ans+=str(round(i,self.n))+','
        ans = ans[:-1]+']'

        return ans
    
  
        

    
if __name__ == '__main__':

    #### HOW To Use:
    ## 1 LOADING A VECTOR
    #a If you know magnitude and angle (degrees)
    A = Vector(mag=0,theta=0)
    print(A)
    print(len(A))

    # #b If you know magnitude and angle (radians)
    # B = Vector(mag=5,theta=pi, deg=False)
    # print(B)

    # #c If you know components
    # C = Vector(3,4)
    # print(C)

    # ##2 ADDING and SUBTRACTING
    # #a Adding
    # D = A+B
    # print(D)

    # #b Subtracting
    # E = C-D
    # print(E)

    # ##3 Multiplying Constants
    # F = 3*E
    # print(F)

    # G = -F
    # print(G)

    # ##4 Dot product (A*B*cos(theta))
    # H = A*B
    # print('Dot product of A*B:',H)

    # ##5 Get Magitude and Direction

    # mag = G.mag()
    # print('Magnitude of G:',mag)

    # dir = G.ang()
    # print('Direction of G:',dir,'degs')

    # dir_rad = G.ang(deg=False)
    # print('Direction of G:',dir_rad,'rads')

    # print(360*sin(50) )