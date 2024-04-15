#!/usr/bin/env python3
import csv
import glob
import numpy as np
import sys
import os

from keras.models import Sequential
from keras.layers import Dense, BatchNormalization, Dropout
from keras.optimizers import Adam
from keras import initializers

SAMPLES_PER_CYCLE = 50
CLASSES = 100

def usage():
    print("Usage: {} <data_dir> <model_name>".format(sys.argv[0]))


def scan_dir(dirname):
    files = sorted(glob.glob("{}/*.csv".format(dirname)))
    csv_files = []
    for fn in files:
        success = True
        with open(fn,"r") as f:
            try:
                lines = f.readlines()
                for l in lines:
                    _ = csv.Sniffer().sniff(l)
            except:
                success = False
        if success:
            csv_files.append(fn)
    return csv_files


def load_data(files):
    train_data_in = None
    train_data_out = None
    val_data_in = None
    val_data_out = None
    classes = []

    current_class = 0
    for fn in files:
        try:
            cls = np.loadtxt(fn,delimiter=",")
            x,y = np.shape(cls)
            t_x = int((7*x)/8)
            v_x = x-t_x
            t_cls = cls[:t_x, ...]
            v_cls = cls[t_x:, ...]
            print("Class:",fn,"Train #:",t_x,"Val #:",v_x)

            if train_data_in is not None:
                train_data_in = np.concatenate((train_data_in,t_cls))
            else:
                train_data_in = np.copy(t_cls)

            if train_data_out is not None:
                tmp = np.full([t_x,CLASSES],0)
                for i in range(0,t_x):
                    tmp[i][current_class] = 1
                train_data_out = np.concatenate((train_data_out,tmp))
            else:
                train_data_out = np.full([t_x,CLASSES],0)
                for i in range(0,t_x):
                    train_data_out[i][current_class] = 1.0

            if val_data_in is not None:
                val_data_in = np.concatenate((val_data_in,v_cls))
            else:
                val_data_in = np.copy(v_cls)

            if val_data_out is not None:
                tmp = np.full([v_x,CLASSES],0)
                for i in range(0,v_x):
                    tmp[i][current_class] = 1
                val_data_out = np.concatenate((val_data_out,tmp))

            else:
                val_data_out = np.full([v_x,CLASSES],0)
                for i in range(0,v_x):
                    val_data_out[i][current_class] = 1.0

            classes.append(fn.split("/")[-1].split(".csv")[0])
            current_class += 1
            if current_class == CLASSES:
                break

        except:
            print("Could not load class: {}".format(fn))
            pass
    return classes,train_data_in, train_data_out, val_data_in, val_data_out

def save_classes(model_name, classes):
    try:
        with open("{}.classes".format(model_name),"w") as f:
            for i in classes:
                f.write(i + "\n")
    except:
        print("Could not save classes!")



def train_network(model_name, train_in, train_out, val_in, val_out):
    model = Sequential()

    model.add(BatchNormalization(scale=False, center=False))
    model.add(Dense(SAMPLES_PER_CYCLE, input_shape=(SAMPLES_PER_CYCLE,), activation='relu',kernel_initializer='random_normal',bias_initializer=initializers.Constant(0.1)))

    model.add(BatchNormalization())
    model.add(Dense(SAMPLES_PER_CYCLE, activation='relu',kernel_initializer='random_normal',bias_initializer=initializers.Constant(0.1)))

    model.add(Dropout(0.1))
    model.add(BatchNormalization())
    model.add(Dense(SAMPLES_PER_CYCLE, activation='sigmoid',kernel_initializer='random_normal',bias_initializer=initializers.Constant(0.1)))


    model.add(Dense(CLASSES, activation='softmax',kernel_initializer='random_normal',bias_initializer=initializers.Constant(0.1)))

    opt = Adam(learning_rate=0.0001)
    model.compile(loss='categorical_crossentropy', optimizer=opt, metrics=['accuracy'])
    model.fit(train_in, train_out, epochs=1000, batch_size=100, shuffle=True)
    _, accuracy = model.evaluate(val_in, val_out)
    print('Validation Accuracy: %.2f' % (accuracy*100))

    return model


def save_model(model,name):
    model.save("{}.keras".format(name), overwrite=True)

def main():
    if len(sys.argv) != 3:
        usage()
        sys.exit(1)
    #os.environ["KERAS_BACKEND"] = "theano"
    files = scan_dir(sys.argv[1])
    classes,train_in, train_out, val_in, val_out = load_data(files)
    print(train_in,train_out)

    save_classes(sys.argv[2],classes)
    model = train_network(sys.argv[2],train_in, train_out, val_in, val_out)
    save_model(model, sys.argv[2])

if __name__ == "__main__":
    main()