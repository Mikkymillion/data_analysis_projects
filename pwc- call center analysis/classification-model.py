
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from lime.lime_tabular import LimeTabularExplainer
import matplotlib.pyplot as plt
df = pd.read_csv('bank-additional-full.csv')

print(df.head(5))

# Drop any unnecessary columns
df = df.drop(['job', 'marital',	'education','default', 'housing', 'loan', 'contact','month', 'day_of_week',	'duration'], axis=1)
print(df.columns)



# Split your data into features (X) and target (y)
X = df[['emp.var.rate', 'cons.price.idx', 'cons.conf.idx', 'euribor3m']]


y = df['y']
print (X)
# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Alternatively, you can train other models like:
# model = RandomForestClassifier()
# model = SVC()
# Train a random forest classifier
rf = RandomForestClassifier()
rf.fit(X_train, y_train)

# Create a LIME explainer
explainer = LimeTabularExplainer(X_train.values, feature_names=X_train.columns, class_names=['no', 'yes'], discretize_continuous=True)

# Explain a prediction
exp = explainer.explain_instance(X_test.values[0], rf.predict_proba, num_features=5)

# Print the explanation
print(exp.as_list())


# Plot the explanation
plt.barh([x[0] for x in exp.as_list()], [x[1] for x in exp.as_list()])
plt.xlabel('Contribution')
plt.ylabel('Feature')
plt.title('Feature Contributions')
plt.show()
