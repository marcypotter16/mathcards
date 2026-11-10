from typing import Tuple, Union

import pyray as rl

class Vector2:
    """A Pythonic wrapper around raylib's Vector2."""
    
    def __init__(
        self, 
        x: float | None = None, 
        y: float | None = None, 
        vect: Union[rl.Vector2, 'Vector2', tuple[float, float], None] = None
    ):
        # Evitiamo di passare argomenti a super() perché pyray/CFFI li gestisce in modo rigido
        super().__init__()
    
        if vect is not None:
            if isinstance(vect, tuple):
                self._x = float(vect[0])
                self._y = float(vect[1])
            else:
                self._x = vect.x
                self._y = vect.y
        else:
            self._x = x if x is not None else 0.0
            self._y = y if y is not None else 0.0
        self.rr = rl.Vector2(self._x, self._y)

    @property
    def raylib_ref(self) -> rl.Vector2:
        return self.rr

    @property
    def x(self) -> float:
        return self._x

    @property
    def y(self) -> float:
        return self._y

    @x.setter
    def x(self, new_x: float):
        self._x = new_x
        self.rr = rl.Vector2(self._x, self._y)

    @y.setter
    def y(self, new_y: float):
        self._y = new_y
        self.rr = rl.Vector2(self._x, self._y)
    
    @staticmethod
    def from_raylib(vec: rl.Vector2) -> 'Vector2':
        """Creates a Python Vector2 from a raylib Vector2."""
        return Vector2(vec.x, vec.y)
    
    def __repr__(self) -> str:
        return f"Vector2({self._x:.2f}, {self._y:.2f})"
    
    def __str__(self) -> str:
        return repr(self)
    
    # Overload operators for easy math
    def __add__(self, other: 'Vector2') -> 'Vector2':
        x = self._x + other._x
        y = self._y + other._y
        return Vector2(x, y)
    
    def __sub__(self, other: 'Vector2') -> 'Vector2':
        return Vector2(self._x - other._x, self._y - other._y)
    
    def __mul__(self, scalar: float) -> 'Vector2':
        return Vector2(self._x * scalar, self._y * scalar)
    
    def __truediv__(self, scalar: float) -> 'Vector2':
        if scalar == 0:
            raise ZeroDivisionError("Cannot divide by zero.")
        return Vector2(self._x / scalar, self._y / scalar)
    
    def __eq__(self, other: 'Vector2') -> bool:
        return self._x == other._x and self._y == other._y
    
    def length(self) -> float:
        return self.mag()

    def mag_sqr(self) -> float:
        return rl.vector2_length_sqr(self.raylib_ref)

    def length_sqr(self) -> float:
        return self.mag_sqr()
    
    def normalize(self) -> 'Vector2':
        length = self.mag()
        if length == 0:
            return Vector2(0, 0)
        return Vector2(self._x / length, self._y / length)

    def normalize_ip(self) -> None:
        length = self.mag()
        self._x /= length
        self._y /= length

    # Moltiplicazione a SINISTRA: scalare * vettore (Es. 0.5 * v)
    def __rmul__(self, scalar: float) -> 'Vector2':
        return self.__mul__(scalar)

    def dot(self, other) -> float:
        return self._x * other.x + self._y * other.y

    def cross(self, other) -> float:
        """Returns the (signed) magnitude of the cross product mathematics.vector"""
        return rl.vector2_cross_product(self.raylib_ref, other)

    def mag(self) -> float:
        return rl.vector2_length(self.raylib_ref)

    def __iter__(self):
        return iter((self.x, self.y))

    def __next__(self):
        return next(iter((self.x, self.y)))

if __name__ == "__main__":
    a = Vector2(vect=rl.Vector2(10, 20))
    print(a)
