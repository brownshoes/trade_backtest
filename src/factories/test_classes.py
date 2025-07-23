class Car:
    def __init__(self, make: str, model: str, year: int):
        self.make = make
        self.model = model
        self.year = year

class Person:
    def __init__(self, name: str, age: int, car: Car):
        self.name = name
        self.age = age
        self.car = car


