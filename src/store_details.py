import re
from numpy import add
import pandas as pd
import time
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
class stores:
    def __init__(self,store_name,driver='chrome',driver_path='/usr/local/bin/chromedriver',zip=44141,headless=True) -> None:
        self.all_addresses=[]
        self.all_distances=[]
        self.all_quants=[]
        self.store_name=store_name
        self.driver_type="chrome"
        self.zip=zip
        CHROMEDRIVER_PATH = driver_path
        s=Service(CHROMEDRIVER_PATH)
        self.chrome_options=Options() 
        if headless:
            self.chrome_options.add_argument("--headless")
        



    def scrape_items(self,debug=False):
        """
        scrape function, no inputs needed because of general attributes of init class.
        """
        self.debug=debug
        self.skus=self._get_skus()
        url=self.skus['url']
        if self.driver_type=='chrome':

            for sku in self.skus['sku_nums']:
                self._parse_skus_(url,sku)
            return self.frames

    def _pretty_data(self):
        """
        helper function that returns list of DFs with all of the information.
        """
        self.frames=[]
        sku_vals=self.skus['sku_nums']
        data={"skus":sku_vals,"addresses":self.all_addresses,"distance":self.all_distances,"quantity":self.all_quants}
        addresses=data['addresses'][0] #this can be hard set since it shouldnt change
        distances=data['distance'][0]  #this can be hard set since it shouldnt change.
        names=self.skus['names']
        for idx,sku in enumerate(sku_vals):
            name=names[idx]
            sku_col=[f"{sku}" for _ in addresses]
            name_col=[f"{name}" for _ in addresses]
            try:
                quant_col=data['quantity'][idx]
                if len(quant_col) != len(addresses):
                    quant_col+=['0']*(len(addresses)-len(quant_col))
            except:
                #there are no tests at all i think?
                quant_col=[0 for i in range(len(addresses))]
            #data integrity check
            if len(distances) != len(addresses):
                distances+=["NA"]*(len(addresses)-len(distances))
            data_dict={"sku":sku_col,"name":name_col,"quants":quant_col,"address":addresses,"distance":distances}
            self.frames.append(pd.DataFrame(data_dict))
        return self.frames



    def _parse_skus_(self,url,sku_num):
        """
        basic selenium things. clicks through the website and passes the source to beautiful soup for further analysis.
        """
        self.driver=webdriver.Chrome(options=self.chrome_options) 
        self.driver.implicitly_wait(3)
        self.driver.get(url)
        if self.debug:
            print("sending keys to sku...")
        sku_form=self.driver.find_element(By.ID,"inventory-checker-form-sku")
        sku_form.send_keys(sku_num)
        if self.debug:
            print("sending keys to zip...")
        zip_form=self.driver.find_element(By.ID,"inventory-checker-form-zip")
        zip_form.send_keys(self.zip)
        if self.debug:
            print("clicking dropdown for quantity...")
        sort_by_button=self.driver.find_element(By.ID,"inventory-checker-form-sort")
        sort_by_button.click()
        if self.store_name == "cvs":
            item=sort_by_button.find_element(By.XPATH,"/html/body/div[1]/div[3]/div[2]/div/main/div/form/div/div[3]/div/div/select/option[3]")
            item.click()
        elif self.store_name=="walmart":
            item=sort_by_button.find_element(By.XPATH,"/html/body/div[1]/div[3]/div[2]/div/main/div/form/div/div[5]/div/div/select/option[4]")
            item.click()
            
        if self.debug:
            print("sending click...")
        button_click=self.driver.find_element(By.CLASS_NAME,'bs-button').click()
        self.driver.implicitly_wait(5)
        html=self.driver.page_source
        self._soup_things(html)
        self._pretty_data()

        self.driver.close()



    def _soup_things(self,html):
        """
        soupify everything and get row data.
        """
        soup=BeautifulSoup(html,"html.parser")
        self._get_table_row(soup)

    def _get_table_row(self,soup):
        """
        grabs individual rows from the website to scrape.
        """


        rows=soup.select("div",{"class":"table__row"})
        addrs=[]
        for row in rows:
            i=row.find("address",{"class":"address"})
            addrs.append(i)
        dists=self._get_distance(soup)
        addrs=self._get_addr(soup)
        quant=self._get_quantity_(soup)
        
        self.all_addresses.append(addrs)
        self.all_distances.append(dists)
        self.all_quants.append(quant)


    def _get_quantity_(self,soup):
        """
        helper function that returns a list of strings of the quantities. I should probably make it a list of floats, but whatever. 
        """
        soup=str(soup)
        quants=re.findall(r"Qty: (\d+)",soup)
        return quants


    def _get_distance(self,soup):
        """
        regex that returns a list of distances in miles
        """
        self.distances=re.findall(r"(\d.+) Miles",str(soup))
        return self.distances


    def _get_addr(self,soup):
        """
        regexs are hard so this is the most overenginered split statement of all time that will return a list of addresses.
        """
        self.div=soup.select_one("table#inventory-checker-table inventory-checker-table--store-availability-price inventory-checker-table--columns-3")
        self.addresses1=soup.find_all('address')
        all_addy=[]
        for addy in self.addresses1:
            experiment=str(addy).replace("<br/>","").split(">")[1].split("<")[0].replace('\n','')
            all_addy.append(experiment)
        return all_addy

    def _get_skus(self):
        """
        helper function that returns a dictionary.

        RETURNS
            dict:
                STORE_NAME,URL,SKU_NUMBERS
        """
        self.store_paths=[
            {"store":'walmart',"url":'https://brickseek.com/walmart-inventory-checker/',"sku_nums":[142089281,373165472,953499978,916411293],
            "names":["BinaxNOW COVID‐19 Antigen Self Test (2 Count)",
            "On/Go COVID-19 Antigen Self-Test - Tech-Enabled, At-Home Covid Test (OTC)- Results in 10 Minutes - 2 Test Kit",
            "Ellume COVID Test Kit, At Home COVID-19 Home Test Kit, Rapid Antigen Self Test, Results in 15 minutes to your free mobile app, FDA Emergency Use Authorization, 1 Pack",
            "InteliSwab™ COVID-19 Rapid Antigen Test, For results anytime and anywhere (2 Tests)"]},
            {"store":"cvs","url":"https://brickseek.com/cvs-inventory-checker/","sku_nums":[550147,823994],"names":["Abbott BinaxNOW COVID-19 Antigen Self Test (2 tests for serial testing)","FlowFlex COVID-19 Antigen Home Test",]},
            {"store":"testing","url":"https://brickseek.com/cvs-inventory-checker/","sku_nums":[550147],"names":["Abbott BinaxNOW COVID-19 Antigen Self Test (2 tests for serial testing)"]}
    ]
        for i in self.store_paths:
            if i['store'] == self.store_name:
                return i

if __name__=="__main__":
    i=stores(store_name='walmart')    
    items=i.scrape_items()