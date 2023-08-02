from kiteconnect import KiteConnect
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import os
from pyotp import TOTP

#Generate and save Request Token
def autologin():
    # Set up KiteConnect API object with API key
    api_key = os.environ.get('Zerodha_API_Key')
    kite = KiteConnect(api_key=api_key)

    # Set up ChromeDriver service and options
    service = webdriver.chrome.service.Service('/usr/local/bin/chromedriver')
    service.start()
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    
    # Open a headless Chrome browser window and navigate to the login page
    driver = webdriver.Remote(service.service_url, options=options)
    driver.get(kite.login_url())
    driver.implicitly_wait(10)
    
    # Find and fill in the login form with user ID and password
    username = driver.find_element(By.XPATH,'/html/body/div[1]/div/div[2]/div[1]/div/div/div[2]/form/div[1]/input')
    password = driver.find_element(By.XPATH,'/html/body/div[1]/div/div[2]/div[1]/div/div/div[2]/form/div[2]/input')
    username.send_keys(os.environ.get('Zerodha_User_ID'))
    password.send_keys(os.environ.get('Zerodha_Password'))
    
    # Submit the login form and find and fill in the TOTP form with the TOTP token
    driver.find_element(By.XPATH,'/html/body/div[1]/div/div[2]/div[1]/div/div/div[2]/form/div[4]/button').click()
    pin = driver.find_element(By.XPATH,'/html/body/div[1]/div/div[2]/div[1]/div[2]/div/div[2]/form/div[1]/input')
    totp = TOTP(os.environ.get('Zerodha_TOTP_Secret'))
    token = totp.now()
    pin.send_keys(token)
    
    # Submit the TOTP form and wait for the request token to appear in the URL
    time.sleep(5)
    request_token=driver.current_url.split('request_token=')[1][:32]
    
    # Write the request token to a file and quit the browser window
    with open('/home/ec2-user/request_token.txt', 'w') as the_file:
        the_file.write(request_token)
    driver.quit()
  
#generating and storing access token in file- valid till 6 am the next day
def store_access_token_in_file():
    request_token = open("/home/ec2-user/request_token.txt",'r').read()
    api_key = os.environ.get('Zerodha_API_Key')
    kite = KiteConnect(api_key=api_key)
    data = kite.generate_session(request_token, api_secret=os.environ.get('Zerodha_API_Secret'))
    with open('/home/ec2-user/access_token.txt', 'w') as file:
            file.write(data.get("access_token"))

#generate trading session and set access token
def generate_trading_session():
    access_token = open('/home/ec2-user/access_token.txt','r').read()
    api_key = os.environ.get('Zerodha_API_Key')
    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(access_token)

#generate trading session by retrieving and storing request and access token
def autologin_all_in_one():

    '''generate trading session by retrieving and storing request and access token'''

    # Set up KiteConnect API object with API key
    api_key = os.environ.get('Zerodha_API_Key')
    kite = KiteConnect(api_key=api_key)
    
    # Set up ChromeDriver service and options
    service = webdriver.chrome.service.Service('/usr/local/bin/chromedriver')
    service.start()
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    
    # Open a headless Chrome browser window and navigate to the login page
    driver = webdriver.Remote(service.service_url, options=options)
    driver.get(kite.login_url())
    driver.implicitly_wait(10)
    
    # Find and fill in the login form with user ID and password
    username = driver.find_element(By.XPATH,'/html/body/div[1]/div/div[2]/div[1]/div/div/div[2]/form/div[1]/input')
    password = driver.find_element(By.XPATH,'/html/body/div[1]/div/div[2]/div[1]/div/div/div[2]/form/div[2]/input')
    username.send_keys(os.environ.get('Zerodha_User_ID'))
    password.send_keys(os.environ.get('Zerodha_Password'))
    
    # Submit the login form and find and fill in the TOTP form with the TOTP token
    driver.find_element(By.XPATH,'/html/body/div[1]/div/div[2]/div[1]/div/div/div[2]/form/div[4]/button').click()
    pin = driver.find_element(By.XPATH,'/html/body/div[1]/div/div[2]/div[1]/div[2]/div/div[2]/form/div[1]/input')
    totp = TOTP(os.environ.get('Zerodha_TOTP_Secret'))
    token = totp.now()
    pin.send_keys(token)
    
    # Submit the TOTP form and wait for the request token to appear in the URL
    time.sleep(7)
    request_token=driver.current_url.split('request_token=')[1][:32]
        
    # Write the request token to a file and quit the browser window
    with open('/home/ec2-user/request_token.txt', 'w') as the_file:
        the_file.write(request_token)
    driver.quit()

    #generating and storing access token in file- valid till 6 am the next day
    data = kite.generate_session(request_token, api_secret=os.environ.get('Zerodha_API_Secret'))
    with open('/home/ec2-user/access_token.txt', 'w') as file:
        file.write(data.get("access_token"))

    #generate trading session and set access token
    kite.set_access_token(data.get("access_token"))


a=0
while a<5:
    try: 
        autologin_all_in_one()
        break
    except:
        a+=1

    
