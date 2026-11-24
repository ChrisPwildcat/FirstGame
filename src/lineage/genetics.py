"""Heritable traits.

Every animal carries a small genome. Offspring take the midpoint of their
parents plus random variation, so whatever pressures decide *who gets to
breed* slowly reshape the whole population -- whether or not the player meant
it to.
"""

from .config import MUTATION


def clamp(v, lo=0.0, hi=1.0):
    return lo if v < lo else hi if v > hi else v


class Genome:
    __slots__ = ("boldness", "aggression", "size")

    def __init__(self, boldness, aggression, size):
        self.boldness = boldness      # tolerance of people -> flight distance
        self.aggression = aggression  # likelihood to attack when close
        self.size = size              # body size -> meat, strength

    @classmethod
    def random(cls, rng, species):
        b_mean, b_sd = species.boldness
        a_mean, a_sd = species.aggression
        return cls(
            clamp(rng.gauss(b_mean, b_sd)),
            clamp(rng.gauss(a_mean, a_sd)),
            clamp(rng.gauss(0.5, 0.1)),
        )

    def child(self, other, rng, mutation=MUTATION):
        b = clamp((self.boldness + other.boldness) / 2 + rng.gauss(0, mutation))
        a = clamp((self.aggression + other.aggression) / 2 + rng.gauss(0, mutation))
        # "Domestication syndrome": selecting for tameness drags other traits
        # along with it. Here, tamer lines trend very slightly smaller.
        s = clamp((self.size + other.size) / 2 + rng.gauss(0, mutation * 0.8)
                  - 0.01 * (b - 0.5))
        return Genome(b, a, s)

    def piebald_chance(self):
        """Patchy coats appear as boldness rises (as in the Belyaev fox study)."""
        return max(0.0, self.boldness - 0.6) * 1.8
