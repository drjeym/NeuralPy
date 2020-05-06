import torch.nn as nn

from collections import OrderedDict


class Sequential():
	__layers = []
	__model = None
	__build = False
	__prev_output_dim = 0

	def __init__(self):
		super(Sequential, self).__init__()

	def __generate_layer_name(self, type, index):
		return f"{type.lower()}_layer_{index+1}"

	def add(self, layer):
		if (self.__build):
			raise Exception("You have built this model already, you can not make any changes in this model")

		if not layer:
			raise Exception("You need to pass a layer")

		self.__layers.append(layer)

	def build(self):
		layers = []

		for index, layer_ref in enumerate(self.__layers):
			if self.__prev_output_dim is not 0:
				layer_ref.get_input_dim(self.__prev_output_dim)

			layer_details = layer_ref.get_layer()

			layer = layer_details["layer"](**layer_details["keyword_arguments"])

			name = layer_details["name"]

			if not name:
				name = self.__generate_layer_name(layer_details["type"], index)

			layers.append((name, layer))

			self.__prev_output_dim = layer_details["n_nodes"]

		self.__model = nn.Sequential(OrderedDict(layers))
		self.__build = True

	def summary(self):
		if self.__build:
			print(self.__model)
			print("Total Number of Parameters: ", sum(p.numel() for p in self.__model.parameters()))
			print("Total Number of Trainable Parameters: ", sum(p.numel() for p in self.__model.parameters() if p.requires_grad))
		else:
			raise Exception("You need to build the model first")