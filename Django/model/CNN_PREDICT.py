
# coding: utf-8

# In[4]:

import numpy as np

np.random.seed(2016)
import os
import glob
import cv2
import datetime
import pandas as pd
import time
import warnings
warnings.filterwarnings("ignore")
from sklearn.cross_validation import KFold
from keras.models import Sequential, load_model
from keras.layers.core import Dense, Dropout, Flatten
from keras.layers.convolutional import Convolution2D, MaxPooling2D, ZeroPadding2D
from keras.preprocessing.image import array_to_img, img_to_array, load_img
from keras.optimizers import SGD
from keras.callbacks import EarlyStopping
from keras.utils import np_utils
from sklearn.metrics import log_loss
from keras import __version__ as keras_version
from random import shuffle
import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import binary_dilation, binary_opening, label
from scipy.spatial import ConvexHull
from skimage.filters import threshold_yen, threshold_triangle
from PIL import Image, ImageDraw

#==============================================================================
# 目标检测
def mask_polygon(verts, shape):
    img = Image.new('L', shape, 0)
    ImageDraw.Draw(img).polygon(verts, outline=1, fill=1)
    mask = np.array(img)
    return mask.T


def convex_hull_mask(data, mask=True):
    segm = np.argwhere(data)
    hull = ConvexHull(segm)
    verts = [(segm[v,0], segm[v,1]) for v in hull.vertices]
    return mask_polygon(verts, data.shape)


def extract_largest_regions(mask, num_regions=2):
    regions, n_labels = label(mask)
    label_list = range(1, n_labels+1)
    sizes = []
    for l in label_list:
        size = (regions==l).sum()
        sizes.append((size, l))
        
    labels = []
    sizes = sorted(sizes, reverse=True)
    
    if sizes :
        #print(sizes)
        num_regions = min(num_regions, n_labels-1)
        min_size = sizes[num_regions][0]

        
        for s, l in sizes:
            if s < min_size:
                regions[regions==l] = 0
            else:
                labels.append(l)
    else :
        print('--------------')

    return regions, labels


def build_binary_opening_structure(binary_image, weight=1):
    s = 1 + 10000 * (binary_image.sum() / binary_image.size) ** 1.4
    s = int(max(12, 3 * np.log(s) * weight))
    return np.ones((s, s))


def simple_detector(o_image):        
    image = np.asarray(o_image)   
    dilation_iterations=40
    num_regions=4
    
    image_array = []
    titles = []

    image_array.append(image.astype('uint8'))
    titles.append('Original')

    # yen
    #threshold = threshold_yen(image)
    threshold = threshold_triangle(image)
    yen = np.zeros_like(image)
    yen[image[:,:,0] > threshold] = image[image[:,:,0] > threshold]

    # denoise
    binary_image = yen[:,:,0] > 0
    structure = build_binary_opening_structure(binary_image)
    binary_image = binary_opening(binary_image, structure=structure)
    binary_image = binary_dilation(binary_image, iterations=dilation_iterations)

    # mask
    regions, labels = extract_largest_regions(binary_image, num_regions=num_regions)
    
    if labels :
        mask = convex_hull_mask(regions>0)
        masked = np.zeros_like(image)
        masked[mask>0,:] = image[mask>0,:]

        titles.append('Whale')
        image_array.append(masked.astype('uint8'))
    
        myImage = Image.fromarray(np.uint8(image_array[1]))
        return myImage
    
    else :
        return o_image
          
#==============================================================================

def load_test(image_path):
    X_test = []
    X_test_id = []
    
    img = load_img(os.path.join(image_path))
    img = simple_detector(img)       
    img = img_to_array(img)
    img = cv2.resize(img, (32, 32), cv2.INTER_LINEAR)       
    X_test.append(img)
    return X_test


def read_and_normalize_test_data(image_path):
    start_time = time.time()
    test_data = load_test(image_path)

    test_data = np.array(test_data, dtype=np.uint8)
    test_data = test_data.transpose((0, 3, 1, 2))

    test_data = test_data.astype('float32')
    test_data = test_data / 255

    #print('Test shape:', test_data.shape)
    #print(test_data.shape[0], 'test samples')
    #print('Read and process test data time: {} seconds'.format(round(time.time() - start_time, 2)))
    return test_data


def dict_to_list(d):
    ret = []
    for i in d.items():
        ret.append(i[1])
    return ret


def merge_several_folds_mean(data, nfolds):
    a = np.array(data[0])
    for i in range(1, nfolds):
        a += np.array(data[i])
    a /= nfolds
    return a.tolist()


def get_validation_predictions(train_data, predictions_valid):
    pv = []
    for i in range(len(train_data)):
        pv.append(predictions_valid[i])
    return pv


def run_cross_validation_process_test(models,image_path):
    batch_size = 16
    num_fold = 0
    yfull_test = []
    test_id = []
    nfolds = len(models)
    test_data = read_and_normalize_test_data(image_path)

    for i in range(nfolds):
        model = models[i]
        num_fold += 1       
        test_prediction = model.predict(test_data, batch_size=batch_size, verbose=0)
        yfull_test.append(test_prediction)

    test_res = merge_several_folds_mean(yfull_test, nfolds)
    return test_res
    #print('--------------------------------------------')
    #print(test_res)

def pred(image_path):
    num_folds = 9
    models = []
    model1 = load_model('F:/code/model_res/model4-dataPreprocessing/Num_folds_9_nb_epoch_30/1.h5')
    models.append(model1)
    model2 = load_model('F:/code/model_res/model4-dataPreprocessing/Num_folds_9_nb_epoch_30/2.h5')
    models.append(model2)
    model3 = load_model('F:/code/model_res/model4-dataPreprocessing/Num_folds_9_nb_epoch_30/3.h5')
    models.append(model3)
    model4 = load_model('F:/code/model_res/model4-dataPreprocessing/Num_folds_9_nb_epoch_30/4.h5')
    models.append(model4)
    model5 = load_model('F:/code/model_res/model4-dataPreprocessing/Num_folds_9_nb_epoch_30/5.h5')
    models.append(model5)
    model6 = load_model('F:/code/model_res/model4-dataPreprocessing/Num_folds_9_nb_epoch_30/6.h5')
    models.append(model6)
    model7 = load_model('F:/code/model_res/model4-dataPreprocessing/Num_folds_9_nb_epoch_30/7.h5')
    models.append(model7)
    model8 = load_model('F:/code/model_res/model4-dataPreprocessing/Num_folds_9_nb_epoch_30/8.h5')
    models.append(model8)
    model9 = load_model('F:/code/model_res/model4-dataPreprocessing/Num_folds_9_nb_epoch_30/9.h5')
    models.append(model9)
    res = run_cross_validation_process_test(models,image_path)
    return res
    
    

if __name__ == '__main__':
    image_path = 'F:/code/data1/train/BET/img_06777.jpg'
    for i in [1,2,3]:
        res = pred(image_path)[0]
        print(res)


# In[ ]:




# In[ ]:


