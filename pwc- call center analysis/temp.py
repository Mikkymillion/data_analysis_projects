import matplotlib.pyplot as plt
import numpy as np
from numpy.random import seed
from sklearn.model_selection import train_test_split
import pandas as pd
import tensorflow
from keras.models import load_model
# from sklearn import preprocessing
import shap
import keras 
from keras.models import Model
from tensorflow.keras.models import load_model
from keras.layers import Input, Dense
from keras import backend as K

import torch
import torch.nn as nn
import torch.nn.functional as F



K.set_session(K.tf.Session(config=K.tf.ConfigProto(intra_op_parallelism_threads=1, inter_op_parallelism_threads=1)))

seed = 123
np.random.seed(seed)
import random
random.seed(seed)



#dataset
dataset = pd.read_csv("cleaned_dataset.csv")

#check it out
print(dataset.head(10))

#training dataset
X = dataset.drop(["y"], axis = 1)
Y = dataset["y"]

#Create training set
X_train, X_other, Y_train, Y_other = train_test_split(X, Y, test_size=0.5, random_state=123)

#Create validation and test set
X_validation, X_test, Y_validation, Y_test = train_test_split(X_other, Y_other, test_size=0.5, random_state=123)


#loading model
model = load_model("model_cyclicalLR.h5", custom_objects={'specificity': specificity, 'precision': precision, 'recall': recall, 'f1_score':f1_score, 'mcc':mcc})



class Metrics(nn.Module):
    def __init__(self):
        super(Metrics, self).__init__()

    def specificity(self, y_true, y_pred):
        # implementation
        pass

    def precision(self, y_true, y_pred):
        # implementation
        pass

    def recall(self, y_true, y_pred):
        # implementation
        pass

    def f1_score(self, y_true, y_pred):
        # implementation
        pass

    def mcc(self, y_true, y_pred):
        # implementation
        pass

# Load model
model = torch.load("model_cyclicalLR.pth", map_location=torch.device('cuda' if torch.cuda.is_available() else 'cpu'))



shap.initjs()
explainer = shap.DeepExplainer(model,X_train[:10].values)

shap_values = explainer.shap_values(X_test.values)
i = 3
shap.force_plot(explainer.expected_value[0].numpy(), shap_values[0][i], features = X_train.iloc[i])

i = 19
shap.force_plot(explainer.expected_value[0].numpy(), shap_values[0][i], features = X_train.iloc[i])

shap.force_plot(explainer.expected_value[0].numpy(), shap_values[0], features = X_train)
shap.summary_plot(shap_values[0],features = X_test,plot_type="dot")



