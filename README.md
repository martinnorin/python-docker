# Create callable web service using Python, Flask, Docker, and Azure.
This guide shows you how to create a callable web service in Python using Flask, Docker and Azure. All code that is displayed is available in the repository.

## Prerequisites
Python (https://www.anaconda.com/download/)

Docker (https://www.docker.com)

Postman (https://www.getpostman.com/)

Azure account (https://azure.microsoft.com)

## Install Python package
After we have installed the prerequisites on the local computer we will proceed to installing the necessary packages. If you don't want to install the packages in your global Python 
installation you can use virtualenv (https://docs.python-guide.org/dev/virtualenvs/) to create a virtual environment that is separated from your global Python installation. That way you 
can isolate your packages from other projects that you are working on.

### Install Flask web server
Flask (http://flask.pocoo.org/) is a microframework that you can use to create web services in Python. This is useful for development but when you want to deploy to production you need a more stable web server. 
Waitress (https://docs.pylonsproject.org/projects/waitress/en/latest/) is a good choice for both Linux and Windows.
The commands to run are:
```
pip install flask
pip install waitress
```

### Install Scikit-learn
In addition to flask you need to install scikit-learn and it's dependencies in order to load existing machine learning models created using scikit-learn.

```
pip install sklearn
pip install numpy
pip install scipy
```

## Create web service endpoints
Create a file named app.py and paste in the following code:

```
from flask import Flask
from waitress import serve

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello World!"
	
# This is important so that the server will run when the docker container has been started. 
# Host=0.0.0.0 needs to be provided to make the server publicly available.
if __name__ == "__main__":
    serve(app,host='0.0.0.0', port=5000)
```

## Run locally
```
python app.py
```

Now you can call your web service endpoint on http://127.0.0.1:5000

If you make any changes you need to shut down the web service by using Ctrl-C and then booting it up again using the same command as above.

## Add POST web service endpoint
Now that we have verified that the web service works we want to add another endpoint that can be used for sending data in the payload. For that we create a POST endpoint:
```
# New imports that can handle requests and json content
from flask import request
import json

@app.route("/do_post", methods=['POST'])
def post_method():
    json = request.get_json()
    name = json["name"]
    age = json["age"]
    return "Hello {}. You're {} years old.".format(name, age)
```

To test this endpoint we need to use Postman with the url http://127.0.0.1:5000/do_post. Make sure that the body is in raw format and sends application/json. Then paste the following into the body and press send:
```
{"name": "John", "age": 23}
```

You will get an answer back:
```
Hello John. You're 23 years old.
```

We now have a functioning web service that can accept JSON formatted data.

## Endpoint for machine learning model
Just to illustrate the point of using an actual machine learning model we will load one from file and make predictions based on the input to the web service.
If you want to create the pickled model you can run iris_train.py which will result in a file named **knn.pkl**. This is a K-Nearest Neighbors classification model of the iris dataset.

```
from sklearn.datasets import load_iris
from sklearn.neighbors import KNeighborsClassifier
from sklearn.externals import joblib

iris = load_iris()
X = iris.data
y = iris.target

knn = KNeighborsClassifier()
knn.fit(X, y)

joblib.dump(knn, "knn.pkl")
```

The endpoint for using the pickled model looks like this:
```
from sklearn.externals import joblib

@app.route("/predict_iris", methods=['POST'])
def predict_iris():
    json = request.get_json()
    # expect X in format [[1, 2, 4, 5]]
    X = json["X"]
    model = joblib.load("knn.pkl")
    return str(model.predict(X))
```

When you call it from Postman with http://127.0.0.1:5000/predict_iris use the following payload:

```
{"X": [[5.1, 3.5, 1.4, 0.2]]}
```

The result should be:
```
[0]
```

## Export Python packages
Before we can create a docker image we need to export the Python packages we have installed in our environment, global or virtual. The command for this is:
```
pip freeze > requirements.txt
```
That create a file named requirements.txt that contains a list of all the packages we have installed.

## Create docker image
The next step is to create a docker image comprised of the Python code we have written. For that we first need to create a docker file named dockerfile.txt.

```
FROM python:3.6

RUN mkdir /code
WORKDIR /code
ADD . /code/
RUN pip install -r ./requirements.txt

EXPOSE 5000
ENV PYTHONPATH="$PYTHONPATH:/code"
CMD ["python", "/code/app.py"]
```

This docker image will be based on Python 3.6 by downloading the docker image from the docker registry. That Python image is quite large, over 2 GB and may include packages 
not needed by you. Another option is python:alpine with is less than 1 GB. Be aware that the Python alpine image may not contain all the packages you need, resulting in strange
error messages when you call your web service.

The docker file will recreate the environment that we have locally including the Python installation and the packages that we need. 
Make sure you are in the same directory as the requirements file when you create the container.

```
docker build -f dockerfile.txt -t python-docker .
```

The image should now be available in your local docker registry. We can verify this by running:

```
docker image ls
```

If you don't have a repository named python-docker with the tag latest, something is wrong and you need to fix your problems before continuing.


## Test docker image locally
After the Docker image has been created successfully we want to test it locally before uploading it to Azure.

```
docker run -d -p 5001:5000 python-docker
```

5001 is the port that will be used when connecting to the web service from outside. 5000 is the container port we defined in the docker file.

If you encounter an error try restarting you Docker service and try again.

## Create Azure Container Registry
If you don't have an existing Container Registry just create one in Azure by following this guide: 
https://docs.microsoft.com/en-us/azure/container-registry/container-registry-get-started-portal

Make sure you have enabled Admin user under Settings -> Access keys. You will be using the username and password on that page for uploading the image to the Registry.

## Upload to Azure Container Registry
Now that you have your Container Registry you login to it:
```
docker login --username <username> --password <password> <login server>
```
Before uploading it to the Container Registry, you need to tag the image using the login server and the name of your local docker image.
``` 
docker tag <local docker image> <login server>/<uploaded docker image name>
```

The last step is to push up the docker image to Container Registry
```
docker push <login server>/<uploaded docker image name>
```

You can now see you image in the Container Registry under Services -> Repositories.  

## Create Azure Container Instance
The final step before you have a callable web service is to create a Container Instance from your uploaded image. You do this in the Azure portal by going to the your Container Registry,
selecting the image and tag, click the three dots and click on Run instance. Enter a valid name and fill in the correct port you used earlier, in this case 5001. Then hit Create.

## Call web service
Now that you have a callable web service for all your machine learning models. You can verify it by calling it from Postman like before. You can find the public IP address from the Container Instance. Don't forget to use the correct port, in this case 5001.
