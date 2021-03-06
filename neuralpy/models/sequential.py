import torch
import numpy as np
from collections import OrderedDict
from .sequential_helper import *


class Sequential:
    def __init__(self, force_cpu=False, training_device=None, random_state=None):
        super(Sequential, self).__init__()
        # Initializing some attributes that we need to function
        self.__layers = []
        self.__model = None
        self.__build = False
        self.__optimizer = None
        self.__loss_function = None
        self.__metrics = None

        # Checking the force_cpu parameter
        if not (force_cpu == True or force_cpu == False):
            raise ValueError(
                f"You have provided an invalid value for the parameter force_cpu")

        # Checking the training_device parameter and comparing it with pytorch device class
        if training_device and not isinstance(training_device, torch.device):
            raise ValueError("Please provide a valid neuralpy device class")

        # Validating random state
        if random_state and not isinstance(random_state, int):
            raise ValueError("Please provide a valid random state")

        # if force_cpu then using CPU
        # if device provided, then using it
        # else auto detecting the device, if cuda available then using it (default option)
        if training_device:
            self.__device = training_device
        elif force_cpu == True:
            self.__device = torch.device("cpu")
        else:
            if torch.cuda.is_available():
                # TODO: currently setting it to cuda:0, may need to change it
                self.__device = torch.device("cuda:0")
            else:
                self.__device = torch.device("cpu")

        # Setting random state if given
        if random_state:
            torch.manual_seed(random_state)

    def __predict(self, X, batch_size):
        # Calling model.eval as we are evaluating the model only
        self.__model.eval()

        # Initializing an empty list to store the predictions
        predictions = torch.Tensor()

        # Conveting the input X to pytorch Tensor
        X = torch.tensor(X)

        if batch_size:
            # If batch_size is there then checking the length and comparing it with the length of input
            if X.shape[0] < batch_size:
                # Batch size can not be greater that sample size
                raise ValueError(
                    "Batch size is greater than total number of samples")

            # Predicting, so no grad
            with torch.no_grad():
                # Spliting the data into batches
                for i in range(0, len(X), batch_size):
                    # Generating the batch from X
                    batch_X = X[i:i+batch_size].float()

                    # Feeding the batch into the model for predictions
                    outputs = self.__model(batch_X)

                    # Appending the data into the predictions tensor
                    predictions = torch.cat((predictions, outputs))
        else:
            # Predicting, so no grad
            with torch.no_grad():
                # Feeding the full data into the model for predictions tensor
                outputs = self.__model(X.float())

                # saving the outputs in the predictions
                predictions = outputs

        # returning predictions tensor
        return predictions

    def add(self, layer):
        # If we already built the model, then we can not a new layer
        if (self.__build):
            raise Exception(
                "You have built this model already, you can not make any changes in this model")

        # Layer verification using the method is_valid_layer
        if not is_valid_layer(layer):
            raise ValueError("Please provide a valid neuralpy layer")

        # Finally adding the layer for layers array
        self.__layers.append(layer)

    def build(self):
        # Building the layers from the layer refs and details
        layers = build_layer_from_ref_and_details(self.__layers)

        # Making the pytorch model using nn.Sequential
        self.__model = torch.nn.Sequential(OrderedDict(layers))

        # Transferring the model to device
        self.__model.to(self.__device)

        # Printing a message with the device name
        print("The model is running on", self.__device)

        # Chanding the build status to True, so we can not make any changes
        self.__build = True

    def compile(self, optimizer, loss_function, metrics=None):
        # To compile a model, first we need to build it, building it first
        if not self.__build:
            # Calling build
            self.build()

        # Checking the optimizer using the method is_valid_optimizer
        if not is_valid_optimizer(optimizer):
            raise ValueError("Please provide a value neuralpy optimizer")

        # Checking the loss_function using the method is_valid_loss_function
        if not is_valid_loss_function(loss_function):
            raise ValueError("Please provide a value neuralpy loss function")

        # Setting metrics
        self.__metrics = metrics

        # Storing the loss function and optimizer for future use
        self.__optimizer = build_optimizer_from_ref_and_details(
            optimizer, self.__model.parameters())
        self.__loss_function = build_loss_function_from_ref_and_details(
            loss_function)

    def fit(self, train_data, test_data, epochs=10, batch_size=32):
        # Ectracting the train and test data from the touples
        X_train, y_train = train_data
        X_test, y_test = test_data

        # If batch_size is there then checking the length and comparing it with the length of training data
        if X_train.shape[0] < batch_size:
            # Batch size can not be greater that train data size
            raise ValueError(
                "Batch size is greater than total number of training samples")

        # If batch_size is there then checking the length and comparing it with the length of training data
        if X_test.shape[0] < batch_size:
            # Batch size can not be greater that test data size
            raise ValueError(
                "Batch size is greater than total number of testing samples")

        # Checking the length of input and output
        if X_train.shape[0] != y_train.shape[0]:
            # length of X and y should be same
            raise ValueError(
                "Length of training Input data and training output data should be same")

        # Checking the length of input and output
        if X_test.shape[0] != y_test.shape[0]:
            # length of X and y should be same
            raise ValueError(
                "Length of testing Input data and testing output data should be same")

        # Conveting the data into pytorch tensor
        X_train = torch.tensor(X_train)
        y_train = torch.tensor(y_train)

        X_test = torch.tensor(X_test)
        y_test = torch.tensor(y_test)

        # Initializing a dict to store the training progress, can be used for viz purposes
        metrics = []

        if self.__metrics is not None:
            metrics = ["loss"] + self.__metrics
        else:
            metrics = ["loss"]

        # Building the history object
        history = build_history_object_for_training(metrics)

        # Running the epochs
        for epoch in range(epochs):
            # Initializing the loss and accuracy with 0
            training_loss_score = 0
            validation_loss_score = 0

            correct_training = 0
            correct_val = 0

            # Training model :)
            self.__model.train()

            # Spliting the data into batches
            for i in range(0, len(X_train), batch_size):
                # Making the batches
                batch_X = X_train[i:i+batch_size].float()
                if "accuracy" in metrics:
                    batch_y = y_train[i:i+batch_size]
                else:
                    batch_y = y_train[i:i+batch_size].float()

                # Moving the batches to device
                batch_X, batch_y = batch_X.to(
                    self.__device), batch_y.to(self.__device)

                # Zero grad
                self.__model.zero_grad()

                # Feeding the data into the model
                outputs = self.__model(batch_X)

                # Calculating the loss
                train_loss = self.__loss_function(outputs, batch_y)

                # Training
                train_loss.backward()
                self.__optimizer.step()

                # Storing the loss val, batchwise data
                training_loss_score = train_loss.item()
                history["batchwise"]["training_loss"].append(train_loss.item())

                # Calculating accuracy
                # Checking if accuracy is there in metrics
                # TODO: Need to do it more dynamic way
                if "accuracy" in metrics:
                    corrects = calculate_accuracy(batch_y, outputs)

                    correct_training += corrects

                    history["batchwise"]["training_accuracy"].append(
                        corrects/batch_size*100)

                    print_training_progress(epoch, epochs, i, batch_size, len(
                        X_train), train_loss.item(), corrects)
                else:
                    print_training_progress(
                        epoch, epochs, i, batch_size, len(X_train), train_loss.item())

            # Evluating model
            self.__model.eval()

            # no grad, no training
            with torch.no_grad():
                # Spliting the data into batches
                for i in range(0, len(X_test), batch_size):
                    # Making the batches
                    batch_X = X_train[i:i+batch_size].float()
                    if "accuracy" in metrics:
                        batch_y = y_train[i:i+batch_size]
                    else:
                        batch_y = y_train[i:i+batch_size].float()

                    # Moving the batches to device
                    batch_X, batch_y = batch_X.to(
                        self.__device), batch_y.to(self.__device)

                    # Feeding the data into the model
                    outputs = self.__model(batch_X)

                    # Calculating the loss
                    validation_loss = self.__loss_function(outputs, batch_y)

                    # Storing the loss val, batchwise data
                    validation_loss_score += validation_loss.item()
                    history["batchwise"]["validation_loss"].append(
                        validation_loss.item())

                    # Calculating accuracy
                    # Checking if accuracy is there in metrics
                    if "accuracy" in metrics:
                        corrects = corrects = calculate_accuracy(
                            batch_y, outputs)

                        correct_val += corrects

                        history["batchwise"]["validation_accuracy"].append(
                            corrects/batch_size*100)

            # Calculating the mean val loss score for all batches
            validation_loss_score /= batch_size

            # Added the epochwise value to the history dict
            history["epochwise"]["training_loss"].append(training_loss_score)
            history["epochwise"]["validation_loss"].append(
                validation_loss_score)

            # Checking if accuracy is there in metrics
            if "accuracy" in metrics:
                # Adding data into hostory dict
                history["epochwise"]["training_accuracy"].append(
                    correct_training/len(X_train)*100)
                history["epochwise"]["training_accuracy"].append(
                    correct_val/len(X_test)*100)

                # Printing a friendly message to the console
                print_validation_progress(
                    validation_loss_score, len(X_train), correct_val)
            else:
                # Printing a friendly message to the console
                print_validation_progress(
                    validation_loss_score, len(X_train))

        # Returning history
        return history

    def predict(self, X, batch_size=None):
        # Calling the __predict method to get the predicts
        predictions = self.__predict(X, batch_size)

        # Returning an numpy array of predictions
        return predictions.numpy()

    def predict_classes(self, X, batch_size=None):
        # Calling the __predict method to get the predicts
        predictions = self.__predict(X, batch_size)

        # Detecting the classes
        predictions = predictions.argmax(dim=1, keepdim=True)

        return predictions.numpy()

    def evaluate(self, X, y, batch_size=None):
        # If batch_size is there then checking the length and comparing it with the length of training data
        if batch_size and X.shape[0] < batch_size:
            # Batch size can not be greater that train data size
            raise ValueError(
                "Batch size is greater than total number of training samples")

        # Checking the length of input and output
        if X.shape[0] != y.shape[0]:
            # length of X and y should be same
            raise ValueError(
                "Length of training Input data and training output data should be same")

        # Calling the __predict method to get the predicts
        predictions = self.__predict(X, batch_size)

        # Converting to tensor
        y_tensor = torch.tensor(y)

        # Calculating the loss
        loss = self.__loss_function(predictions, y_tensor)

        # if metrics has accuracy, then calculating accuracy
        if "accuracy" in self.__metrics:
            # Calculating no of corrects
            corrects = calculate_accuracy(y_tensor, predictions)

            # Calculating accuracy
            accuracy = corrects / len(X) * 100

            # Returning loss and accuracy
            return {
                'loss': loss.item(),
                'accuracy': accuracy
            }

        # Returning loss
        return {
            'loss': loss
        }

    def summary(self):
        # Printing the model summary using pytorch model
        if self.__build:
            # Printing models summary
            print(self.__model)

            # Calculating total number of params
            print("Total Number of Parameters: ", sum(p.numel()
                                                      for p in self.__model.parameters()))

            # Calculating total number of trainable params
            print("Total Number of Trainable Parameters: ", sum(p.numel()
                                                                for p in self.__model.parameters() if p.requires_grad))
        else:
            raise Exception("You need to build the model first")

    def get_model(self):
        # Returning the pytorch model
        return self.__model

    def set_model(self, model):
        # Checking if model is None
        if model is None:
            raise ValueError("Please provide a valid pytorch model")

        # Saving the model
        self.__model = model
        self.__build = True
