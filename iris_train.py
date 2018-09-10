from sklearn.datasets import load_iris
from sklearn.neighbors import KNeighborsClassifier
from sklearn.externals import joblib

iris = load_iris()
X = iris.data
y = iris.target

knn = KNeighborsClassifier()
knn.fit(X, y)

joblib.dump(knn, "knn.pkl")