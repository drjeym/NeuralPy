import pytest
from torch.nn import Tanh as _Tanh
from neuralpy.activation_functions import Tanh

# Possible values
names = [False, 12, 3.6, -2]

@pytest.mark.parametrize(
	"name", 
	[(name) for name in names]
)
def test_relu_should_throw_value_error_Exception(name):
    with pytest.raises(ValueError) as ex:
        x = Tanh(name=name)

# Possible values
names = ["test1", "test2"]

@pytest.mark.parametrize(
    "name", 
    [(name) for name in names]
)
def test_tanh_get_input_dim_and_get_layer_method(name):
    x = Tanh(name=name)

    assert x.get_input_dim(12) == None

    details = x.get_layer()

    assert isinstance(details, dict) == True

    assert details["n_inputs"] == None

    assert details["n_nodes"] == None

    assert details["name"] == name

    assert issubclass(details["layer"], _Tanh) == True

    assert details["keyword_arguments"] == None