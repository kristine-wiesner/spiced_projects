import Customer
from datetime import time
class Supermarket:
    def __init__(self, customers):
        self.customers = customers
        self.time = time (8,0)

        
    def get_time(self):
        return self.time
    
    def next_minute(self):
        self.time = time(self.time.hour, self.time.minute +1 )
        for c in self.customers:
            c.next_state()
        
    def print_customers(self):
        for c in self.customers:
            print(c)
        print('----------')
        
    def is_active(self):
        for c in self.customers:
            if (c.is_active()):
                return True
        return False
    
    def __repr__(self):
        self.print_customers()
        return f'{len(self.customers)} customers running around at {self.time}'

        