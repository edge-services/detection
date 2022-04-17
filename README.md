# Edge Detection Service - (Image Classifier)

## WORK IN PROGRESS

This repository can be used as a reference to creating ML or Deep learning models using Tensorflow, Keras or any library of your choice.  This one has code for creating Image classifier model that runs on IBM Watson Machine learning platform and can be configured to use runtime (CPU or GPU) as per your choice.  All the code to create and train the model is under the "build_code" folder.  Please note that whole of this code under "build_code" folder is zipped and deployed to IBM Watson Machine Learning platform and runs there.  

## RUN LOCALLY

  - Create virtual environment and activate it

```

virtualenv venv -p python3.8
source venv/bin/activate

#pip freeze > requirements.txt
pip install -r requirements.txt

```

### DEACTIVATE AND DELETE VIRTUAL ENV

```

deactivate
rmvirtualenv venv

```
