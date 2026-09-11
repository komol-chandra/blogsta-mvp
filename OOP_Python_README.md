# Object-Oriented Programming (OOP) in Python — Study Guide

A structured reference for learning OOP concepts using Python. Each section includes the concept, why it matters, and runnable code examples.

---

## Table of Contents

1. [Classes & Objects](#1-classes--objects)
2. [Attributes](#2-attributes)
3. [Methods](#3-methods)
4. [Encapsulation](#4-encapsulation)
5. [Inheritance](#5-inheritance)
6. [Polymorphism](#6-polymorphism)
7. [Abstraction](#7-abstraction)
8. [Dunder (Magic) Methods](#8-dunder-magic-methods)
9. [Composition](#9-composition)
10. [Multiple Inheritance & MRO](#10-multiple-inheritance--mro)
11. [Suggested Learning Path](#suggested-learning-path)
12. [Practice Project Ideas](#practice-project-ideas)

---

## 1. Classes & Objects

**Concept:** A *class* is a blueprint. An *object* (or instance) is a concrete thing built from that blueprint.

```python
class Car:
    def __init__(self, brand, model):
        self.brand = brand
        self.model = model

my_car = Car("Toyota", "Corolla")   # object / instance
print(my_car.brand)                 # Toyota
```

**Key terms:**
- `class` — the keyword that defines a blueprint
- `__init__` — the constructor, runs automatically when an object is created
- `self` — refers to the specific instance being worked on
- **instance** — a single object created from a class

---

## 2. Attributes

**Concept:** Data stored on a class or object.

- **Instance attributes** — unique to each object, usually set in `__init__`
- **Class attributes** — shared across *all* instances of the class

```python
class Car:
    wheels = 4                      # class attribute — same for every Car

    def __init__(self, brand):
        self.brand = brand          # instance attribute — unique per object

car1 = Car("Honda")
car2 = Car("Ford")
print(car1.wheels, car2.wheels)     # 4 4 (shared)
print(car1.brand, car2.brand)       # Honda Ford (different)
```

⚠️ **Common pitfall:** mutable class attributes (like lists) are shared across instances unless explicitly overridden in `__init__`.

---

## 3. Methods

**Concept:** Functions defined inside a class. Three types:

| Type | Decorator | First Param | Use case |
|---|---|---|---|
| Instance method | none | `self` | Operates on one object's data |
| Class method | `@classmethod` | `cls` | Operates on the class itself; alt constructors |
| Static method | `@staticmethod` | none | Utility logic grouped in the class, no state needed |

```python
class Car:
    def __init__(self, brand, model):
        self.brand = brand
        self.model = model

    def honk(self):                          # instance method
        return f"{self.brand} says Beep!"

    @classmethod
    def from_string(cls, car_str):            # class method (alt constructor)
        brand, model = car_str.split("-")
        return cls(brand, model)

    @staticmethod
    def is_valid_year(year):                  # static method
        return 1900 <= year <= 2026

car = Car.from_string("Toyota-Corolla")
print(Car.is_valid_year(2020))                # True
```

---

## 4. Encapsulation

**Concept:** Restricting direct access to internal data, exposing a controlled interface instead.

Python doesn't have true "private" like Java, but uses naming conventions:

| Prefix | Meaning |
|---|---|
| `name` | Public — accessible anywhere |
| `_name` | Protected (convention only) — "internal use" |
| `__name` | Private (name-mangled) — hard to access from outside |

```python
class BankAccount:
    def __init__(self, balance):
        self._balance = balance     # protected by convention
        self.__pin = 1234           # name-mangled (becomes _BankAccount__pin)

    @property
    def balance(self):              # controlled read access
        return self._balance

    @balance.setter
    def balance(self, amount):      # controlled write access
        if amount < 0:
            raise ValueError("Balance cannot be negative")
        self._balance = amount

account = BankAccount(1000)
account.balance = 1500              # goes through the setter
print(account.balance)              # 1500
```

**Why it matters:** prevents invalid states (e.g., negative balances) and hides implementation details so they can change later without breaking external code.

---

## 5. Inheritance

**Concept:** A class (child/subclass) reuses and extends the behavior of another class (parent/superclass).

```python
class Vehicle:
    def __init__(self, brand):
        self.brand = brand

    def describe(self):
        return f"A {self.brand} vehicle"

class Car(Vehicle):                 # Car inherits from Vehicle
    def __init__(self, brand, doors):
        super().__init__(brand)     # call parent constructor
        self.doors = doors

    def describe(self):             # method overriding
        return f"{super().describe()} with {self.doors} doors"

c = Car("Toyota", 4)
print(c.describe())                 # A Toyota vehicle with 4 doors
```

**Key terms:**
- `super()` — calls the parent class's version of a method
- **method overriding** — child class redefines a parent's method
- **is-a relationship** — a `Car` *is a* `Vehicle`

---

## 6. Polymorphism

**Concept:** Different classes respond to the same method call in their own way.

```python
class Dog:
    def speak(self):
        return "Woof"

class Cat:
    def speak(self):
        return "Meow"

animals = [Dog(), Cat()]
for animal in animals:
    print(animal.speak())           # Woof, Meow — same call, different result
```

This also applies via inheritance (overriding a parent method) or via **duck typing** — Python doesn't check the type, only whether the method exists:

> "If it walks like a duck and quacks like a duck, it's a duck."

```python
def make_it_speak(thing):
    return thing.speak()            # works for ANY object with .speak()
```

---

## 7. Abstraction

**Concept:** Hiding *how* something works, exposing only *what* it does. Enforced in Python using `abc` (Abstract Base Classes).

```python
from abc import ABC, abstractmethod

class Shape(ABC):
    @abstractmethod
    def area(self):
        pass                        # no implementation — subclasses MUST provide one

class Circle(Shape):
    def __init__(self, radius):
        self.radius = radius

    def area(self):
        return 3.14159 * self.radius ** 2

# shape = Shape()      # ❌ Error: Can't instantiate abstract class
circle = Circle(5)
print(circle.area())   # ✅ 78.53975
```

**Why it matters:** guarantees that every subclass implements required behavior — useful for defining contracts/interfaces (similar to Java interfaces or PHP contracts).

---

## 8. Dunder (Magic) Methods

**Concept:** Special methods (double underscore = "dunder") that let your custom objects work with Python's built-in syntax (`print()`, `==`, `+`, `len()`, etc).

```python
class Point:
    def __init__(self, x, y):
        self.x, self.y = x, y

    def __str__(self):                          # controls print(obj) / str(obj)
        return f"({self.x}, {self.y})"

    def __repr__(self):                          # controls repr(obj), debugging
        return f"Point({self.x}, {self.y})"

    def __eq__(self, other):                     # controls obj1 == obj2
        return self.x == other.x and self.y == other.y

    def __add__(self, other):                    # controls obj1 + obj2
        return Point(self.x + other.x, self.y + other.y)

    def __len__(self):                            # controls len(obj)
        return 2

p1, p2 = Point(1, 2), Point(3, 4)
print(p1)              # (1, 2)  -- uses __str__
print(p1 + p2)          # (4, 6)  -- uses __add__
print(p1 == Point(1, 2))  # True  -- uses __eq__
```

**Commonly used dunders:**

| Method | Triggered by |
|---|---|
| `__init__` | Object creation |
| `__str__` | `print(obj)`, `str(obj)` |
| `__repr__` | Debug representation |
| `__eq__` | `==` |
| `__lt__` | `<` (sorting) |
| `__add__` | `+` |
| `__len__` | `len(obj)` |
| `__getitem__` | `obj[key]` |
| `__iter__` | `for x in obj` |
| `__call__` | `obj()` — makes object callable like a function |

---

## 9. Composition

**Concept:** Building objects out of *other* objects rather than through inheritance. Often summarized as "has-a" instead of "is-a."

```python
class Engine:
    def start(self):
        return "Engine started"

class Car:
    def __init__(self):
        self.engine = Engine()      # Car "has-a" Engine (composition)

    def start(self):
        return self.engine.start()

car = Car()
print(car.start())                  # Engine started
```

**Composition vs Inheritance — when to use which:**

| Use Inheritance when... | Use Composition when... |
|---|---|
| There's a true "is-a" relationship | There's a "has-a" / "uses-a" relationship |
| Subclass genuinely extends parent behavior | You want to combine independent, reusable pieces |
| The hierarchy is stable and unlikely to change | You need flexibility to swap parts at runtime |

> Rule of thumb: **"Favor composition over inheritance"** — it usually leads to more flexible, less tightly-coupled code.

---

## 10. Multiple Inheritance & MRO

**Concept:** Python allows a class to inherit from more than one parent class (Java and PHP restrict this to interfaces only).

```python
class Flyer:
    def move(self):
        return "Flying"

class Swimmer:
    def move(self):
        return "Swimming"

class Duck(Flyer, Swimmer):         # inherits from BOTH
    pass

d = Duck()
print(d.move())                     # "Flying" — resolved via MRO
```

**MRO (Method Resolution Order):** the rule Python uses to decide *which* parent's method to use when there's a conflict. You can inspect it with:

```python
print(Duck.__mro__)
# (<class 'Duck'>, <class 'Flyer'>, <class 'Swimmer'>, <class 'object'>)
```

Python resolves left-to-right, depth-first, based on the order parents are listed in the class definition.

---

## Suggested Learning Path

1. ✅ Classes & Objects → Attributes → Methods
2. ✅ Encapsulation
3. ✅ Inheritance
4. ✅ Polymorphism
5. ✅ Abstraction (ABCs)
6. ✅ Dunder methods
7. ✅ Composition
8. ✅ Multiple inheritance / MRO

Spend roughly **1–2 days per concept**, writing small standalone scripts before moving to the next.

---

## Practice Project Ideas

Once you've covered the concepts individually, reinforce them with a small project that uses most/all of them together:

- **Library Management System** — `Book`, `Member`, `Library` classes; inheritance for `EBook`/`PrintBook`; encapsulation for due dates/fines
- **Simple E-Commerce Cart** — `Product`, `Cart`, `Order`; composition (`Cart` has `Product`s); dunder methods (`__add__` to combine carts, `__len__` for item count)
- **Zoo / Animal Simulation** — abstract `Animal` base class; polymorphism via `speak()`/`move()`; multiple inheritance for hybrid behaviors
- **Bank System** — encapsulation-heavy (`SavingsAccount`, `CheckingAccount` inheriting from `Account`); abstraction for `Account` as a base contract

---

*This guide is meant as a living reference — revisit and expand it as you build projects and encounter new patterns.*
