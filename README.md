BME688 devkit ML Experiments

keras ML experiments for classification of gases using the Bosch BME688 devkit (the BLE ESP32-based with 8 BME688 sensors).
======================================================================


BoardConfiguration.bmeconfig needs to be copied on the devkit SD card. It contains the heater profiles and duty cycle configuration required to train the model.

Unlike the Bosch AI Studio, we use all the consecutive runs within a duty cycle to train the model, not just the values of a single run at different heating profiles. This is due to different chemical compounds in the air taking different time to alter the sensor resistance values.


Two models are used, one fully connected with two hidden layers and a second one that uses a CNN layer and two fully-connected layers.

The CNN model generally performs better.

Warning: IT IS OF CRITICAL IMPORTANCE TO HAVE REPRODUCIBLE SAMPLING. Samples should be taken at the same distance from the source, preferably using the same setup.


The model allows up to 100 classes. The example trained one has just several classes.


How to train:

python3 read_class.py <work_dir> <class_name> <samples>


where: 

work_dir - model directory (e.g "Fruits")
class_name - the name of the class (e.g "Lemon")
samples - the number of sensor run samples. 50 should be OK, the more the better, but it takes more time


How to train the model:

python3 train_model.py <data_dir> <model_name>

or

python3 train_model_cnn.py <data_dir> <model_name>

where:

data_dir - model directory 
model_name - the name of your model (you can use the same one as the model directory name)


How to do inference:

python3 inference.py <model_name>

or

python3 inference_cnn.py <model_name>

where:
model_name - the model name



More on BME688 devkit and software: https://www.bosch-sensortec.com/software-tools/software/bme688-software/