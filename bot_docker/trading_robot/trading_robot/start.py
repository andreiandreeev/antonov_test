#!/usr/bin/env python
# coding: utf-8

# In[1]:

from __future__ import print_function
import json
import numpy as np
import mysql.connector
import time
import openapi_client
from openapi_client.rest import ApiException
from pprint import pprint
from robot import Robot



robot = Robot()


# In[3]:


robot.import_config()


# In[4]:


robot.start(1000)


# In[ ]:




