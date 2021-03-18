#!/usr/bin/env python
# coding: utf-8

# In[11]:

import json
import numpy as np
import time
import threading
import mysql.connector
import openapi_client
from openapi_client.rest import ApiException

unit_testing = True

class Robot:
    '''Traiding bot class. 
       REQUIRES CONFIGURATION!
       
       To configure the bot class constructor or json config file can be used.
    '''
    def __init__(self, gap = np.nan, gap_ignore = np.nan, use_database = False, client_id = 'not configured', client_secret = 'not configured', test_mode = True):
       
        '''
        If you want to configure robot using class constructor you should pass following parameters: 
    
        gap: float -- gap trading strategy parameter
        gap_ignore: float -- gap_ignore trading strategy parameter
        client_id: string -- api key that can be found on deribit website
        client_server: string -- api secret that can be found on deribit website
        test_mode: bool -- use testnet !optional!, default: True 
        '''
        self.__gap = gap                     
        self.__gap_ignore = gap_ignore       
        self.__client_id = client_id         
        self.__client_secret = client_secret 
        self.__use_database = use_database	
        self.__state = 1 #defines current stradegy state
      
        if test_mode:
            self.__host = "https://test.deribit.com/api/v2"
        else:
            self.__host = "https://deribit.com/api/v2"
    
    def get_config(self):
        '''
        Returns host value and configuration parameters except test_mode
        '''
        return self.__gap, self.__gap_ignore, self.__client_id, self.__client_secret, self.__host
    
    def export_config(self, config_file = 'config.json'):
        '''
        Exports host value and configuration parameters except test_mode to .json file
        ROBOT SHOULD BE CONFIGURED BEFORE CALLING THIS FUNCTION!
        
        Params: 
        config_file: string -- relative path to output config file !optional!, default: 'config.json'
        
        '''
        assert not np.isnan(self.__gap),                     "Gap is not configured!"
        assert not np.isnan(self.__gap_ignore),              "Gap Ignore is not configured!"
        assert not self.__client_id == 'not configured',     "Client ID is not configured!"
        assert not self.__client_secret == 'not configured', "Client Secret is not configured!"

        with open(config_file, 'w') as json_file:
            json.dump({'robot' :{
                             'gap': self.__gap,
                             'gap_ignore': self.__gap_ignore}, 
                       'exchange' :{
                             'host': self.__host,
                             'client_id': self.__client_id,
                             'client_secret': self.__client_secret}},\
                      json_file)
   

    def import_config(self, config_file = 'config.json'):
        '''
        Imports host value and configuration parameters except test_mode to .json file
       
        Params: 
        config_file: string -- relative path to input config file !optional!, default: 'config.json'
        
        '''
        with open(config_file) as json_file:
            data = json.load(json_file)
            
        self.__gap           = data['robot']['gap']
        self.__gap_ignore    = data['robot']['gap_ignore']
        self.__client_id     = data['exchange']['client_id']
        self.__client_secret = data['exchange']['client_secret']
        self.__host          = data['exchange']['host']
        
        assert not np.isnan(self.__gap),                     "Gap is not configured!"
        assert not np.isnan(self.__gap_ignore),              "Gap Ignore is not configured!"
        assert not self.__client_id == 'not configured',     "Client ID is not configured!"
        assert not self.__client_secret == 'not configured', "Client Secret is not configured!" 
        assert not self.__host          == 'not configured', "Host is not configured!" 
   
    
    def create_connection(self):
        '''
        Connects to deribit api and prescribes access token to bot
        ROBOT SHOULD BE CONFIGURED BEFORE CALLING THIS FUNCTION!
        '''
        assert not self.__client_id == 'not configured',     "Client ID is not configured!"
        assert not self.__client_secret == 'not configured', "Client Secret is not configured!" 
        assert not self.__host          == 'not configured', "Host is not configured!" 
        
        configuration = openapi_client.Configuration()
        configuration.host = self.__host
        configuration.access_token = self.__client_id

        auth_api_instance = openapi_client.AuthenticationApi(openapi_client.ApiClient(configuration))
       
        grant_type = 'client_credentials' 
        client_id = self.__client_id 
        client_secret = self.__client_secret
        scope = 'trade:read_write'
        
        try:
            api_response = auth_api_instance.public_auth_get(grant_type, '', '', client_id, client_secret, '', '', '',  scope=scope)
            
        except ApiException as e:
            print("Exception when calling AuthenticationApi->public_auth_get: %s\n" % e)

        self.__access_token = api_response['result']['access_token']

                    
    def open_order(self, order_type: str, price: float):
        '''
        Opens buy or sell order with specified price
        ROBOT SHOULD BE CONFIGURED BEFORE CALLING THIS FUNCTION!
        
        Params: 
        order_type: string -- type of order, possible values: 'buy', 'sell'
        price: float -- price in which order is placed, should be positive
        '''
        
        assert order_type == 'buy' or order_type == 'sell', "Order type should be 'buy' or 'sell'!"
        
        self.create_connection()
        
        configuration = openapi_client.Configuration()
        configuration.access_token = self.__access_token
        configuration.host = self.__host        
        
        api_instance = openapi_client.PrivateApi(openapi_client.ApiClient(configuration))
       
        instrument_name = 'BTC-PERPETUAL' 
        amount = 10
        type = 'limit' 
        label = 'label_example'
        price = price 
        time_in_force = 'good_til_cancelled'
        max_show = 10 
        post_only = 'true' 
        reduce_only = 'false' 

        
        try:
            if order_type == 'buy':
                api_response = api_instance.private_buy_get(instrument_name, amount, type=type, label=label, price=price, time_in_force=time_in_force, max_show=max_show, post_only=post_only, reduce_only=reduce_only)
            else:
                api_response = api_instance.private_sell_get(instrument_name, amount, type=type, label=label, price=price, time_in_force=time_in_force, max_show=max_show, post_only=post_only, reduce_only=reduce_only)
               
        except ApiException as e:
            print("Exception when calling PrivateApi->private_buy_get: %s\n" % e)

        if order_type == 'buy':
            self.__buy_price = price
        else:
            self.__sell_price = price
           
   
    def are_orders_closed(self):
        '''
        Shows if all the orders are closed
        ROBOT SHOULD BE CONFIGURED BEFORE CALLING THIS FUNCTION!
        
        Return value: bool
        True if all orders are closed
        False else
        '''
            
        self.create_connection()
        
        configuration = openapi_client.Configuration()
        configuration.access_token = self.__access_token
        configuration.host = self.__host

        api_instance = openapi_client.PrivateApi(openapi_client.ApiClient(configuration))
        instrument_name = 'BTC-PERPETUAL' # str | Instrument name
        type = 'all' # str | Order type, default - `all` (optional)

        try:
            # Retrieves list of user's open orders within given Instrument.
            api_response = api_instance.private_get_open_orders_by_instrument_get(instrument_name, type=type)
        except ApiException as e:
            print("Exception when calling PrivateApi->private_get_open_orders_by_instrument_get: %s\n" % e)
        
        return len(api_response['result']) == 0
        
    def cancel_orders(self):
        '''
        Cancels all opened orders
        ROBOT SHOULD BE CONFIGURED BEFORE CALLING THIS FUNCTION!

        '''
        self.create_connection()
        
        configuration = openapi_client.Configuration()
        configuration.access_token = self.__access_token
        configuration.host = self.__host
        
        api_instance = openapi_client.PrivateApi(openapi_client.ApiClient(configuration))

        try:
            api_response = api_instance.private_cancel_all_get()
        except ApiException as e:
            print("Exception when calling PrivateApi->private_cancel_all_get: %s\n" % e)
        

    def get_price(self):
       
        '''
        Shows current mark price 
        ROBOT SHOULD BE CONFIGURED BEFORE CALLING THIS FUNCTION!
        
        Return value: float
        Current mark price
        
        '''
        self.create_connection()
        
        configuration = openapi_client.Configuration()
        configuration.access_token = self.__access_token
        configuration.host = self.__host


        api_instance = openapi_client.PublicApi(openapi_client.ApiClient(configuration))
        instrument_name = 'BTC-PERPETUAL'
        depth = 1 

        try:
            # Retrieves the order book, along with other market values for a given instrument.
            api_response = api_instance.public_get_order_book_get(instrument_name, depth=depth)
            return api_response['result']['mark_price']
        except ApiException as e:
            print("Exception when calling PublicApi->public_get_order_book_get: %s\n" % e)
            
    def start(self, iterations: int):
        '''
        Clears bot state and starts trading routine
        ROBOT SHOULD BE CONFIGURED BEFORE CALLING THIS FUNCTION!
        
        iterations: int -- how many iterations of trading routine to perform
        '''
        
        assert not np.isnan(self.__gap),                     "Gap is not configured!"
        assert not np.isnan(self.__gap_ignore),              "Gap Ignore is not configured!"
        assert not self.__client_id == 'not configured',     "Client ID is not configured!"
        assert not self.__client_secret == 'not configured', "Client Secret is not configured!" 
        assert not self.__host          == 'not configured', "Host is not configured!"
        
        counter = iterations
        
        self.clear_state()
        
        while counter > 0:
            self.trade()
            counter -= 1
        
        if self.__use_database:
            self.log_orders()

        self.clear_state()
        
        
    def trade(self):
        '''
        Performs trading routine
        ROBOT SHOULD BE CONFIGURED BEFORE CALLING THIS FUNCTION!
        
        '''
        assert not np.isnan(self.__gap),                     "Gap is not configured!"
        assert not np.isnan(self.__gap_ignore),              "Gap Ignore is not configured!"
        assert not self.__client_id == 'not configured',     "Client ID is not configured!"
        assert not self.__client_secret == 'not configured', "Client Secret is not configured!" 
        assert not self.__host          == 'not configured', "Host is not configured!" 
        
        current_price = self.get_price()
    
        
        if self.__state == 1:
            self.open_order('buy', current_price - self.__gap/2)
            self.__state = 2
        
        if self.__state == 2:
            if current_price < self.__buy_price and self.are_orders_closed:
                self.__state = 3
            elif current_price > self.__buy_price + self.__gap + self.__gap_ignore:
                self.cancel_orders()
                self.__state = 1
        
        if self.__state == 3:
            self.open_order('sell', current_price + self.__gap)
            self.__state = 4

        if self.__state == 4:
            if current_price > self.__buy_price and self.are_orders_closed:
                self.__state = 1
            elif current_price < self.__buy_price - self.__gap - self.__gap_ignore:
                self.cancel_orders()
                self.__state = 3

        
    
    def clear_state(self):
        '''
        Clears bot state -- buy_price, sell_price and state and cancels all opened orders
        ROBOT SHOULD BE CONFIGURED BEFORE CALLING THIS FUNCTION!
        
        '''
        self.log_orders()
        self.__buy_price = np.nan 
        self.__sell_price = np.nan
        self.__state = 1
        self.cancel_orders()

    def get_orders(self):
        '''
        Gets historical orders data 
        ROBOT SHOULD BE CONFIGURED BEFORE CALLING THIS FUNCTION!
        
        '''        
        self.create_connection()
        
        configuration = openapi_client.Configuration()
        configuration.access_token = self.__access_token
        configuration.host = self.__host

        api_instance = openapi_client.PrivateApi(openapi_client.ApiClient(configuration))
        instrument_name = 'BTC-PERPETUAL' 
        count = 100
        offset = 0 
        include_old = 'true'
        include_unfilled = 'true'

        try:
            # Retrieves list of user's open orders within given Instrument.
            api_response = api_instance.private_get_order_history_by_instrument_get(instrument_name, count=count, offset=offset, include_old=include_old, include_unfilled=include_unfilled)
        except ApiException as e:
            print("Exception when calling PrivateApi->private_get_open_orders_by_instrument_get: %s\n" % e)
        
        self.__orders = api_response['result']
    
    
    def log_orders(self):
        '''
        Log orders into a database
        ROBOT SHOULD BE CONFIGURED BEFORE CALLING THIS FUNCTION!
        
        '''
       # cnx = mysql.connector.connect(user='root', password='QmBvbNzn64', database='orders')
        #cursor = cnx.cursor()
        
        #self.get_orders()
        #for order in self.__orders:
        #    cursor.execute("INSERT INTO orders (id, type, price, amount, status) VALUES (%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE status=%s;", (order['order_id'], order['direction'], order['price'], order['amount'], order['order_state'], order['order_state']))
        #    cnx.commit()


# In[12]:


if unit_testing:
    test_robot = Robot()
    test_robot.import_config()
    
    
    '''UNIT TEST 1. CHECK CLEAR_STATE'''
    test_robot.clear_state()
    assert test_robot.are_orders_closed(), "Unit test 1 'clear_state' failed. "
    print("Unit test 1 'clear_state' passed.")
    
    '''UNIT TEST 2. CHECK OPEN_ORDER'''
    test_robot.open_order('buy', 1)
    assert not test_robot.are_orders_closed(), "Unit test 2 'open_order' failed. "
    print("Unit test 2 'open_order' passed.")
    
    '''UNIT TEST 3. CHECK CANCEL_ORDERS'''
    test_robot.cancel_orders()
    assert test_robot.are_orders_closed(), "Unit test 3 'cancel_orders' failed. "
    print("Unit test 3 'cancel_orders' passed.")

    '''UNIT TEST 4. CHECK IMPORT/EXPORT_CONFIG'''
    test_robot.export_config('test_config.json')
    test_robot2 = Robot()
    test_robot2.import_config('test_config.json')
    assert test_robot.get_config() == test_robot2.get_config(), "Unit test 4 'import/export_config' failed. "
    print("Unit test 4 'import/export_config' passed.") 


# In[ ]:




