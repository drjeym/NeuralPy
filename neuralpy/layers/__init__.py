"""Layers are the building blocks of a Neural Network.
A complete Neural Network model consists of several layers.
A Layer is a function that receives a tensor as output,
computes something out of it, and finally outputs a tensor.

NeuralPy currently supports only one type of Layer and
that is the Dense layer.
"""

from .dense import Dense
