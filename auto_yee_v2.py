#router ARP table scraper - to find if android device is on device list
import selenium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from time import sleep
from subprocess import check_output as cmdout
from subprocess import CalledProcessError
import subprocess
import yeelight
from yeelight import Bulb
from yeelight import BulbException
import requests
from datetime import datetime
from datetime import timedelta



#attribution to https://sunrise-sunset.org/api

def action_bulb(bulb, bulb_turned_on_once, sun_times, in_arp):
    for i in range(10):
        try:
            if (bulb.get_properties()['power'] == 'off'
                and not bulb_turned_on_once
                and not is_daylight(sun_times))
                and in_arp:
                bulb.turn_on()
                file = open('yeelight log.txt', '+a')
                file.write('bulb turned on ' + str(time.localtime()) + '\n')
                return True
            if bulb.get_properties()['power'] == 'on'
                and not in_arp:
                bulb.turn_off()
                file = open('yeelight log.txt', '+a')
                file.write('bulb turned off ' + str(time.localtime()) + '\n')
                return True
        except BulbException as e:
            print(e)
            sleep(2)
    raise


def bulb():
    for i in range(10):     
        try:
            bulb_list = yeelight.discover_bulbs()
            bulb_ip = bulb_list[0]['ip']
            result = Bulb(bulb_ip)
            print('bulb info got')
            return bulb
        except BulbException as e:
            print(e)
            sleep(2)
    
            

def sunrise_scrape(sun_times, start_time):
    current_time = time.time()
    if not sun_times  or (current_time -  start_time) > 86400:
        for i in range(10):
            try:
                response = requests.get('https://api.sunrise-sunset.org/json?lat=-27.54987&lng=152.912788').json()
                print('got response formatting...')
                sunrise = datetime.strptime(response['results']['sunrise'], '%I:%M:%S %p')
                sunrise = sunrise + timedelta(hours = 10)
                sunset = datetime.strptime(response['results']['sunset'], '%I:%M:%S %p')
                sunset = sunset + timedelta(hours = 10)
                sun_times = [sunrise, sunset]
                print('loaded sun times ')
                return sun_times
            except:
                sleep(2)
    else:
        return sun_times

def is_daylight(sun_times):
    sunrise = datetime.time(sun_times[0])
    sunset = datetime.time(sun_times[1])
    now = datetime.time(datetime.today())
    if now > sunrise and now < sunset:
        return True
    if now < sunrise:
        return False
    if now > sunset:
        return False
    else:
        print('This should never happen, something weird is going on')
####### Phone pinging ########

def arp_scrape():
    opts = Options()
    opts.set_headless()
    assert opts.headless    #check if headless is active
    browser =  webdriver.Chrome(options = opts)
    for i in range(10):
        try:
            browser.get('http://192.168.0.1/main.html?loginuser=1')
            browser.switch_to_frame('menufrm') #switch to menu frame
            browser.find_element_by_id('1').click() #click menu buttons
            browser.find_element_by_id('10').click()
            browser.switch_to.default_content() #switch out of menu frame
            browser.switch_to_frame('basefrm')
            arp = browser.find_elements_by_tag_name('td')
            print('done accessing table')
            mac_list = []
            ip_list = []
            for i in arp[6:-1:4]:
                mac_list.append(i.text)
            for i in arp[4:-1:4]:
                ip_list.append(i.text)
            browser.close()
            if 'b4:f7:a1:e7:8b:99' in mac_list:
                index = mac_list.index('b4:f7:a1:e7:8b:99')
                phone_ip = ip_list[index]
                print('Phone IP address is ' + phone_ip)
                return phone_ip
            else:
                print('Can\'t find phone on router ARP table')
                return False
        except:
            sleep(2)
    raise
    print('cannot scrape')
        
        
def ping(ip):
    try:
        result = str(cmdout('ping -w 1000 ' + ip))
        received = result[result.index('Received') + 11]
        print(received + ' packets received')
        return True
    except subprocess.CalledProcessError:
        print('no ping response')
        return False
    
def checkarp(ip):
    for i in range(10):
        try:
            result = str(cmdout('arp -a'))
            if ip in result:
                print('found in ARP')
                return True
            else:
                print('Not in ARP')
                return False
        except CalledProcessError as e:
            sleep(2)
    raise

def main():
    sun_times = None 
    open('yeelight log.txt', 'w').close     #to clear the log
    start_time = time.time()
    away_ping_count = 0     #sets variable that count no. pings no phone detected
    while True:
        sun_times = sunrise_scrape(sun_times, start_time)
        bulb_turned_on_once = True #initialize bulb turned on once status
        if away_ping_count < 4:
            pass
        else:
            bulb_turned_on_once = False
        ip = arp_scrape()
        print('scrape done')
        ping(ip)    #to refresh arp
        if ip:
            bulb_object = bulb()
            if checkarp(ip):
                away_ping_count = 0
                action_bulb(bulb_object,bulb_turned_on_once,sun_times, True)
            else:
                away_ping_count += 1
                print('ping count is ' + str(away_ping_count))
                for i in range(10):
                    try:
                        if bulb.get_properties()['power'] == 'on' and not bulb_turned_on_once:
                            bulb.turn_off()
                            file = open('yeelight log.txt', '+a')
                            file.write('bulb turned off ' + str(time.localtime()) + '\n')
                        print ('No phone on network')
                        break
                    except:
                        sleep(2)
                else:
                    print('nor responding to pings but in ARP')
                    pass
        else:
            print('Problem with scraping')
