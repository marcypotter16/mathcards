
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Generic, Literal, Protocol, TypeVar, Any, runtime_checkable

from mathematics.vector import Vector2

T_contra = TypeVar("T_contra", contravariant=True)
T_co = TypeVar("T_co", covariant=True)

@runtime_checkable
class SupportsAdditionAndFloatMul(Protocol[T_contra, T_co]):
    def __add__(self, other: T_contra, /) -> T_co: ...
    def __mul__(self, other: float, /) -> T_co: ...

TweenableT = TypeVar("TweenableT", bound=SupportsAdditionAndFloatMul[Any, Any])

class TweenMode(Enum):
    CHAIN = 0
    PARALLEL = 1

@dataclass
class TweenParams(Generic[TweenableT]):
    target:                     Any
    property_name:              str
    end:                        TweenableT
    start:                      TweenableT | None   = None
    dur:                        float               = 1.0
    easing_type:                Literal[
                                'linear', 
                                'ease-in-quad', 
                                'ease-out-quad', 
                                'ease-in-out-quad', 
                                'ease-in-cubic', 
                                'ease-out-cubic', 
                                'ease-in-out-cubic'
    ]                                               = 'ease-in-out-cubic'
    autostart:                  bool                = True
    repeat:                     bool                = False
    how_many_times:             int                 = 0 # if repeat is True it repeats n times, if n is 0 it repeats until stop() is called
    mode:                       TweenMode           = TweenMode.PARALLEL
    callback:                   Callable | None     = None
    
class Tween:
    def __init__(self, tp: TweenParams[TweenableT]) -> None:
        self.params = tp
        if tp.target is None:
            raise ValueError("Tween target is None")
        if not hasattr(tp.target, tp.property_name):
            raise ValueError(f"Target {tp.target} doesn't have property {tp.property_name}")
        # If start is not defined, use the current value of the property 
        # as a starting value
        if tp.start is None:
            self.params.start = getattr(tp.target, tp.property_name)
        self.current_time = 0.0
        self.finished = True
        self.paused = False
        self.how_many_times_completed = 0
        if self.params.autostart:
            self.restart()

    def restart(self):
        self.current_time = 0.0
        self.finished = False

    def stop(self):
        self.finished = True
        self.current_time = 0.0

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

    def update(self, dt: float):
        if not self.finished and not self.paused:
            self.current_time += dt
            if self.current_time >= self.params.dur:
                self.current_time = self.params.dur
                self.finished = True
                if self.params.callback is not None:
                    self.params.callback()
                self.how_many_times_completed += 1
                if self.params.repeat:
                    if self.params.how_many_times == 0 or self.how_many_times_completed <= self.params.how_many_times:
                        self.restart()
            # current = getattr(self.params.target, self.params.property_name)
            new_value = self.evaluate()
            setattr(self.params.target, self.params.property_name, new_value)

    def _get_eased_alpha(self, elapsed_time: float) -> float:
        if self.params.dur <= 0:
            return 1.0
        
        # 1. Tempo passato / Durata totale (Valore normalizzato tra 0.0 e 1.0)
        t = max(0.0, min(1.0, elapsed_time / self.params.dur))
        
        # 2. Applica la distorsione temporale in base all'easing scelto
        if self.params.easing_type == 'linear':
            return t
        
        elif self.params.easing_type == 'ease-in-quad':
            return t * t
        
        elif self.params.easing_type == 'ease-out-quad':
            return t * (2.0 - t)
        
        elif self.params.easing_type == 'ease-in-out-quad':
            return 2.0 * t * t if t < 0.5 else -1.0 + (4.0 - 2.0 * t) * t
        
        elif self.params.easing_type == 'ease-in-cubic':
            return t * t * t
        
        elif self.params.easing_type == 'ease-out-cubic':
            t -= 1.0
            return t * t * t + 1.0

        elif self.params.easing_type == 'ease-in-out-cubic':
            if t < 0.5:
                return 4.0 * t * t * t
            else:
                return 1.0 - ((-2.0 * t + 2.0) ** 3) / 2.0
            
        return t

    def evaluate(self):
        alpha = self._get_eased_alpha(self.current_time)
        # start + (elapsed_time/total_time) * (end - start) is equivalent to:
        # (if alpha=elapsed/total):
        # start + alpha * end - alpha * start =
        # start * (1 - alpha) + end * alpha
        return self.params.start * (1 - alpha) + self.params.end * alpha # type: ignore

class TweenManager:
    def __init__(self) -> None:
        self.tweens: dict[str, list[Tween]] = {}

    def add_tween(self, t: Tween, kill_existing=False):
        key = f"{id(t.params.target)}.{t.params.property_name}"
        if not key in self.tweens.keys():
            self.tweens[key] = [t]
            return

        # TODO: This has to be rewritten better because we are not checking
        # if mode is PARALLEL or CHAIN but for now whatever
        if kill_existing:
            self.tweens.pop(key)
            
        if t.params.mode == TweenMode.PARALLEL:
            if not key in self.tweens.keys():
                self.tweens[key] = [t]
                return
            self.tweens[key].append(t)


        # CHAINING NOT YET IMPLEMENTED
        elif t.params.mode == TweenMode.CHAIN:
            # self.tweens.append(t)
            print("-- ERROR: tween chaining not yet implemented")

    def update(self, dt: float):
        keys_to_remove = []

        for key, tween_list in self.tweens.items():
            # 1. Update all tweens first
            for tween in tween_list:
                tween.update(dt)
            
            # 2. Filter the list in-place to keep ONLY the ones that are NOT finished
            # This avoids the index-shifting bug entirely
            self.tweens[key] = [tween for tween in tween_list if not tween.finished]
            
            # 3. Mark the key for deletion if its list is now empty
            if len(self.tweens[key]) == 0:
                keys_to_remove.append(key)

        # 4. Safely clean up empty dictionary keys after the main iteration is done
        for key in keys_to_remove:
            self.tweens.pop(key)

if __name__ == "__main__":
    class Empty:
        def __init__(self) -> None:
            self.position: Vector2 = Vector2(0, 0)
    o = Empty()
    a = Vector2(0, 0)
    o.position = a
    b = Vector2(1, 10)
    t = Tween(TweenParams(o, "position", end=b, dur=2.0, easing_type='linear'))
    tm = TweenManager()
    tm.add_tween(t)
    for _ in range(120):
        tm.update(1/60)
        print(o.position)