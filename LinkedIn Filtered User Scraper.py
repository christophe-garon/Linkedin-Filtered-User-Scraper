#!/usr/bin/env python
# coding: utf-8

# In[1]:


#required installs (i.e. pip3 install in terminal): pandas, selenium, bs4, and possibly chromedriver(it may come with selenium)
#Download Chromedriver from: https://chromedriver.chromium.org/downloads
#To see what version to install: Go to chrome --> on top right click three dot icon --> help --> about Google Chrome
#Move the chrome driver to (/usr/local/bin) -- open finder -> Command+Shift+G -> search /usr/local/bin -> move from downloads

from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup as bs
import time
import os
from datetime import datetime
import pandas as pd
import re
import caffeine
import random
import schedule
import gender_guesser.detector as gender
d = gender.Detector()
import collections
import matplotlib.pyplot as plt
import openpyxl
from openpyxl import load_workbook
get_ipython().run_line_magic('matplotlib', 'inline')
caffeine.on(display=True)

page_url = input("Enter the Company Linkedin URL: ")
company_name = "cardiologists"

try:
    f= open("{}/{}_credentials.txt".format(company_name,company_name),"r")
    contents = f.read()
    username = contents.replace("=",",").split(",")[1]
    password = contents.replace("=",",").split(",")[3]
    page = int(contents.replace("=",",").split(",")[5])
    
except:
     if os.path.isdir(company_name) == False:
        try:
            os.mkdir(company_name)
        except OSError:
            print ("Creation of the directory %s failed" % company_name)
        else:
            print ("Successfully created the directory %s " % company_name)

        f= open("{}/{}_credentials.txt".format(company_name,company_name),"w+")
        username = input('Enter your linkedin username: ')
        password = input('Enter your linkedin password: ')
        page = 1
        f.write("username={}, password={}, page_index={}, page_url={}".format(username,password,page,page_url))
        f.close()


# In[2]:


#Get any existing scraped data
try:
    scraped = pd.read_csv("{}/{}_linkedin_backup.csv".format(company_name,company_name))
    liker_names = list(scraped["Id"])
    user_gender = list(scraped["Gender"])
    liker_locations = list(scraped["Location"])
    liker_headlines = list(scraped["Headline"])
    user_bios = list(scraped["Bio"])
    est_ages = list(scraped["Age"])
    influencers = list(scraped["Followed Influencers"])
    companies = list(scraped["Followed Companies"])
except:
    liker_names = []
    user_gender = []
    liker_locations = []
    liker_headlines = []
    user_bios = []
    est_ages = []
    influencers = []
    companies = []
    pass

#Get the Meta Data
try:
    linkedin_pages = pd.read_csv("meta_data.csv")
    interest_pages = list(linkedin_pages["Interest Pages"])
    follower_counts = list(linkedin_pages["Follower Counts"])
    follow_rate = list(linkedin_pages["Follow Rate"])
except:
    interest_pages = []
    follower_counts = []
    follow_rate = []


# In[3]:


#access Webriver
browser = webdriver.Chrome('chromedriver')

#Open login page
browser.get('https://www.linkedin.com/login?fromSignIn=true&trk=guest_homepage-basic_nav-header-signin')

#Enter login info:
elementID = browser.find_element_by_id('username')
elementID.send_keys(username)

elementID = browser.find_element_by_id('password')
elementID.send_keys(password)
#Note: replace the keys "username" and "password" with your LinkedIn login info
elementID.submit()


# In[4]:


# #Go to webpage
browser.get(page_url +"&page={}".format(page))


# In[5]:


#code to narrow down search specs


# In[6]:


try:
    wb = pd.read_excel("{}/{}_activities.xlsx".format(company_name,company_name))
    post_dates = list(wb['Date Posted'])
    post_texts = list(wb['Post Text'])
    post_likes = list(wb['Post Likes'])
    post_comments = list(wb['Post Comments'])
    video_views = list(wb['Video Views'])
    media_links = list(wb['Media Links'])
    media_types = list(wb['Media Type'])
    frequency = list(wb['Frequency'])
    
except: 
    
    #define the variables we want
    post_dates = []
    post_texts = []
    post_likes = []
    post_comments = []
    video_views = []
    media_links = []
    media_types = []
    frequency = []


# In[7]:


def scroll():
    #Simulate scrolling to capture all posts
    SCROLL_PAUSE_TIME = random.randint(1,3)

    # Get scroll height
    last_height = browser.execute_script("return document.body.scrollHeight")

    while True:
        # Scroll down to bottom
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait to load page
        time.sleep(SCROLL_PAUSE_TIME)

        # Calculate new scroll height and compare with last scroll height
        new_height = browser.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height


# In[8]:


#Scrolls up the main page
def scroll_up():
    #Simulate scrolling to capture all posts
    SCROLL_PAUSE_TIME = 1.5

    # Get scroll height
    last_height = browser.execute_script("return document.body.scrollHeight")

    while True:
        # Scroll down to bottom
        browser.execute_script("window.scrollTo(0, -document.body.scrollHeight);")

        # Wait to load page
        time.sleep(SCROLL_PAUSE_TIME)

        # Calculate new scroll height and compare with last scroll height
        new_height = browser.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height


# In[9]:


#Scrolls popups
def scroll_popup(class_name):
    #Simulate scrolling to capture all posts
    SCROLL_PAUSE_TIME = 1.5

    # Get scroll height
    js_code = "return document.getElementsByClassName('{}')[0].scrollHeight".format(class_name)
    last_height = browser.execute_script(js_code)

    while True:
        # Scroll down to bottom
        path = "//div[@class='{}']".format(class_name)
        browser.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", browser.find_element_by_xpath(path))

        # Wait to load page
        time.sleep(SCROLL_PAUSE_TIME)

        # Calculate new scroll height and compare with last scroll height
        new_height = browser.execute_script(js_code)
        if new_height == last_height:
            break
        last_height = new_height


# In[10]:


#Function that estimates user age based on earliest school date or earlier work date
def est_age():

    browser.switch_to.window(browser.window_handles[1])
    date = datetime.today()
    current_year = date.strftime("%Y")
    school_start_year = "9999"
    work_start_year = "9999"

    #Get page source
    user_profile = browser.page_source
    user_profile = bs(user_profile.encode("utf-8"), "html")


    #Look for earliest university start date
    try:
        grad_year = user_profile.findAll('p',{"class":"pv-entity__dates t-14 t-black--light t-normal"})
        
        if grad_year == []:
            browser.execute_script("window.scrollTo(0, 1000);")
            user_profile = browser.page_source
            user_profile = bs(user_profile.encode("utf-8"), "html")
            grad_year = user_profile.findAll('p',{"class":"pv-entity__dates t-14 t-black--light t-normal"})
            
        
        for d in grad_year:
            year = d.find('time').text.strip().replace(' ', '')
            start_year = re.sub(r'[a-zA-Z]', r'', year)
            start_year = start_year[0:4]
            if start_year < school_start_year:
                        school_start_year = start_year
    except:
        pass
    

    #Look for earlies work date
    try:
        #Click see more if it's there
        try:
            browser.find_element_by_xpath("//button[@class='pv-profile-section__see-more-inline pv-profile-section__text-truncate-toggle link-without-visited-state']").click()
        except:
            time.sleep(1)
            pass

        work_start = user_profile.findAll('h4', {"class":"pv-entity__date-range t-14 t-black--light t-normal"})


        for d in work_start:
            start_date = d.find('span',class_=None)
            start_date = start_date.text.strip().replace(' ', '')
            start_date = re.sub(r'[a-zA-Z]', r'', start_date)
            start_year = start_date[0:4]
            if start_year < work_start_year:
                    work_start_year = start_year
    except:
        pass

    # Compare work and school start dates to avoid adult degress
    if school_start_year < work_start_year:
        #Estimate age based on avg university start age of 18
        est_birth_year = int(school_start_year) - 18
        est_age = int(current_year) - est_birth_year

    else:
        #Estimate age based on avg post college work start date of 22
        est_birth_year = int(work_start_year) - 22
        est_age = int(current_year) - est_birth_year

    if est_age <= 0:
        est_age = 'unknown'
    
    return est_age
        


# In[11]:


#Function that Scrapes user data
def get_user_data(user_profile):
    
    global skip_count

    try:
        name = user_profile.find('li',{'class':"inline t-24 t-black t-normal break-words"})
        name = name.text.strip()
    except:
        print("This is a company. Skipping for now.")
        return
    
    #Make sure liker isn't a duplicate
    if name not in liker_names:

        skip_count = 0
        liker_names.append(name)
        split_name = name.split(" ", 2)
        #Get Liker Gender
        user_gender.append(d.get_gender(split_name[0])+"^ ")

        try:
            #Get Liker Location
            location = user_profile.find('li',{'class':"t-16 t-black t-normal inline-block"})
            liker_locations.append(location.text.strip()+"^ ")
        except:
            liker_locations.append("No Location")

        try:
            #Get Liker Headline
            headline = user_profile.find('h2',{"class":"mt1 t-18 t-black t-normal break-words"})
            liker_headlines.append(headline.text.strip())
        except:
            liker_headlines.append("No Headline")


        #Get Liker Bio
        try:
            browser.find_element_by_xpath("//a[@id='line-clamp-show-more-button']").click()
            time.sleep(2)
            user_profile = browser.page_source
            user_profile = bs(user_profile.encode("utf-8"), "html")
            bio = user_profile.findAll("span",{"class":"lt-line-clamp__raw-line"})
            user_bios.append(bio[0].text.strip())
        except:
            try:
                bio_lines = []
                bios = user_profile.findAll('span',{"class":"lt-line-clamp__line"})
                for b in bios:
                    bio_lines.append(b.text.strip())
                bio = ",".join(bio_lines).replace(",", ". ")
                user_bios.append(bio)

            except:
                user_bios.append('No Bio')
                pass

        #Get estimated age using our age function
        age = est_age()
        est_ages.append(age)


        
        #Click see more on user interests
        try:
            time.sleep(2)
            interest_path = "//a[@data-control-name='view_interest_details']"
            browser.find_element_by_xpath(interest_path).click()
        except:
            scroll()
            time.sleep(2)
            try:
                interest_path = "//a[@data-control-name='view_interest_details']"
                browser.find_element_by_xpath(interest_path).click()
            except:
                influencers.append("No Influencers^ ")
                companies.append("No Companies^ ")
                return

        time.sleep(1)

        #Scrape the influencers the user follows
        try:
            influencer_path = "//a[@id='pv-interests-modal__following-influencers']"
            browser.find_element_by_xpath(influencer_path).click()

            #Scroll the end of list
            class_name = 'entity-all pv-interests-list ml4 pt2 ember-view'
            #interest_box_path = "//div[@class='entity-all pv-interests-list ml4 pt2 ember-view']"
            scroll_popup(class_name)

            influencer_page = browser.page_source
            influencer_page = bs(influencer_page.encode("utf-8"), "html")
            influencer_list = influencer_page.findAll("li",{"class":"entity-list-item"})


            user_influencers = ""
            for i in influencer_list:
                name = i.find("span",{"class":"pv-entity__summary-title-text"})
                name = name.text.strip()
                user_influencers += name + "^ "
                cleaned_name = name.replace(",","")
                
                if cleaned_name not in interest_pages:
                    interest_pages.append(cleaned_name)
                    follower_count = i.find('p', {"class":"pv-entity__follower-count"}).text.strip()
                    follower_count = follower_count.split(' ')
                    follower_count = follower_count[0]
                    follower_counts.append(follower_count)
                    
                    #Calc the follower rate
                    total_linkedin_users = 260000000
                    follow_percent = float(follower_count.replace(",",""))/total_linkedin_users * 100
                    follow_rate.append(follow_percent)

            influencers.append(user_influencers)


        except:
            influencers.append("No Influencers^ ")



        #Scrape the companies the user follows
        try:
            company_path = "//a[@id='pv-interests-modal__following-companies']"
            browser.find_element_by_xpath(company_path).click()

            time.sleep(1)

            #Scroll the end of list
            class_name = 'entity-all pv-interests-list ml4 pt2 ember-view'
            #interest_box_path = "//div[@class='entity-all pv-interests-list ml4 pt2 ember-view']"
            scroll_popup(class_name)


            company_page = browser.page_source
            company_page = bs(company_page.encode("utf-8"), "html")
            company_list = company_page.findAll("li",{"class":"entity-list-item"})


            user_companies = ""
            for i in company_list:
                name = i.find("span",{"class":"pv-entity__summary-title-text"})
                name = name.text.strip()
                user_companies += name + "^ "
                cleaned_name = name.replace(",","")
                
                if cleaned_name not in interest_pages:
                    interest_pages.append(cleaned_name)
                    follower_count = i.find('p', {"class":"pv-entity__follower-count"}).text.strip()
                    follower_count = follower_count.split(' ')
                    follower_count = follower_count[0]
                    follower_counts.append(follower_count)
                    
                    #Calc the follower rate
                    total_linkedin_users = 260000000
                    follow_percent = float(follower_count.replace(",",""))/total_linkedin_users * 100
                    follow_rate.append(follow_percent)

            companies.append(user_companies)
                

        except:
            companies.append("No Companies^ ")

    else:
        skip_count+=1
        print("already scaped this user.")
        time.sleep(random.randint(1,2))
        return
        


# In[12]:


def scrape_post(container):

    global post_dates 
    global post_texts 
    global post_likes
    global post_comments
    global video_views 
    global media_links 
    global media_types
    global frequency

    try:

        #Get Post Text
        post_text = "None"
        try:
            text_box = container.find("div",{"class":"feed-shared-update-v2__description-wrapper ember-view"})   
            post_text = text_box.text.strip()     
        except:
            pass
            

        #Get Post type and Link    
        media_link = "None"
        media_type = "Unknown"
        try:
            video_box = container.findAll("div",{"class": "feed-shared-update-v2__content feed-shared-linkedin-video ember-view"})
            video_link = video_box[0].find("video", {"class":"vjs-tech"})
            media_link = video_link['src']
            media_type = "Video"
        except:
            try:
                image_box = container.findAll("div",{"class": "feed-shared-image__container"})
                image_link = image_box[0].find("img", {"class":"ivm-view-attr__img--centered feed-shared-image__image feed-shared-image__image--constrained lazy-image ember-view"})
                media_link = image_link['src']
                media_type = "Image"
            except:
                try:
                    #mutiple shared images
                    image_box = container.findAll("div",{"class": "feed-shared-image__container"})
                    image_link = image_box[0].find("img", {"class":"ivm-view-attr__img--centered feed-shared-image__image lazy-image ember-view"})
                    media_link = image_link['src']
                    media_type = "Multiple Images"
                except:
                    try:
                        article_box = container.findAll("div",{"class": "feed-shared-article__description-container"})
                        article_link = article_box[0].find('a', href=True)
                        media_link = article_link['href']
                        media_type = "Article"
                    except:
                        try:
                            video_box = container.findAll("div",{"class": "feed-shared-external-video__meta"})          
                            video_link = video_box[0].find('a', href=True)
                            media_link = video_link['href']
                            media_type = "Youtube Video" 
                        except:
                            try:
                                poll_box = container.findAll("div",{"class": "feed-shared-update-v2__content overflow-hidden feed-shared-poll ember-view"})
                                media_type = "Other: Poll, Shared Post, etc"
                            except:
                                pass
             
            
        #if this is a duplicate only update frequency
        if post_text in post_texts and post_text != "None":
                frequency[post_texts.index(post_text)] +=1
                return
        elif media_link in media_links and media_link != "None":
                frequency[media_links.index(media_link)] +=1
                return
        else:
            post_texts.append(post_text)
            media_links.append(media_link)
            media_types.append(media_type)
            frequency.append(1)  
            
            
        #Get post date
        try:
            post_date = container.find("span",{"class":"feed-shared-actor__sub-description t-12 t-normal t-black--light"}) 
            post_dates.append(post_date.text.strip()[0:-2])
        except:
            post_dates.append("None")
            
            
            
        #Check for likes and comments and append amount   
        try:
            new_likes = container.findAll("li", {"class":"social-details-social-counts__reactions social-details-social-counts__item"})
        except:
            new_likes = "None"
          
        try:
            new_comments = container.findAll("li", {"class": "social-details-social-counts__comments social-details-social-counts__item"})
        except:
            new_comments = "None"




        #Getting Video Views. (The folling three lines prevents class name overlap)
        view_container2 = set(container.findAll("li", {'class':["social-details-social-counts__item"]}))
        view_container1 = set(container.findAll("li", {'class':["social-details-social-counts__reactions","social-details-social-counts__comments social-details-social-counts__item"]}))
        result = view_container2 - view_container1

        view_container = []
        for i in result:
            view_container += i

        try:
            video_views.append(view_container[1].text.strip().replace(' Views',''))
        except:
            video_views.append('N/A')


        try:
            post_likes.append(new_likes[0].text.strip())
        except:
            post_likes.append(0)
            pass

        try:
            post_comments.append(new_comments[0].text.strip())                           
        except:                                                           
            post_comments.append(0)
            pass

    except:
        pass


# In[13]:


def word_counter(words):
    wordcount = {}
    for word in words.split('^ '):
        word = word.replace("\"","")
        word = word.replace("!","")
        word = word.replace("â€œ","")
        word = word.replace("â€˜","")
        word = word.replace("*","")
        word = word.replace("?","")
        word = word.replace("mostly_male","male")
        word = word.replace("mostly_female","female")
        
        exclude_words = ["No Influencers", "No Companies", "unknown", "andy", ""]
        
        if word not in exclude_words:
            if word not in wordcount:
                wordcount[word] = 1
            else:
                wordcount[word] += 1
        else:
            pass
            
    return wordcount


# In[14]:


def get_df(wc):
    
    total_scraped = len(user_gender)
    
    trimmed_count = collections.Counter(wc).most_common(300)

    words = []
    count = []
    percent = []
    interest_index = []
    interest_diff = []
    for item in trimmed_count:
        words.append(item[0])
        count.append(item[1])
        
    for c in count:
        percent.append(round(((c/total_scraped) * 100), 2))
    
    #make interest dictionary from meta data
    interest_dict = dict(zip(interest_pages, follow_rate))
            
    n=0
    for w in words:
        if w in list(interest_dict.keys()):
            if float(interest_dict[w]) != 0:
                index = float(percent[n])/float(interest_dict[w])
                interest_index.append(round(index,2))
                interest_diff.append(round(float(percent[n])-float(interest_dict[w]),2))
                n+=1
            else:
                interest_index.append("NA")
                interest_diff.append("NA")
                n+=1
        else:
            interest_index.append("NA")
            interest_diff.append("NA")
            n+=1
        

    data = {"Word": words,"Count": count, "Percentage": percent, "Index":interest_index, "Absolute Difference":interest_diff}

    df = pd.DataFrame(data, index =None)
    return df


# In[15]:


def clean_list(interest):
    clean_list = []
    for item in interest:
        clean = item.replace('^','')
        clean_list.append(clean.title())
    return clean_list


# In[16]:


def clean_interests(interest):
    clean_list = []
    for item in interest:
        clean = item.replace('^',',')
        clean_list.append(clean)
    return clean_list


# In[17]:


def count_interests():
    company_list = ",".join(companies).replace(',','')
    company_count = word_counter(company_list)
    common_companies = get_df(company_count)

    influencer_list = ",".join(influencers).replace(',','')
    influencer_count = word_counter(influencer_list)
    common_influencers = get_df(influencer_count)
    
    gender_list = ",".join(user_gender).replace(',','')
    gender_count = word_counter(gender_list)
    common_genders = get_df(gender_count)

    location_list = ",".join(liker_locations).replace(',','')
    location_count = word_counter(location_list)
    common_locations = get_df(location_count)
    
    return common_companies, common_influencers, common_genders, common_locations


# In[18]:


def plot_interests(df1,df2,df3,df4):
    company_plot = df1[0:24].plot.barh(x='Word',y='Percentage')
    company_plot.invert_yaxis()
    company_plot.set_ylabel('Companies')
    company_plot.figure.savefig("{}/c_plot.png".format(company_name), dpi = 100, bbox_inches = "tight")

    influencer_plot = df2[0:24].plot.barh(x='Word',y='Percentage')
    influencer_plot.invert_yaxis()
    influencer_plot.set_ylabel('Influencers')
    influencer_plot.figure.savefig("{}/i_plot.png".format(company_name), dpi = 100, bbox_inches = "tight")
    
    gender_plot = df3[0:24].plot.barh(x='Word',y='Percentage')
    gender_plot.invert_yaxis()
    gender_plot.set_ylabel('Gender')
    gender_plot.figure.savefig("{}/g_plot.png".format(company_name), dpi = 100, bbox_inches = "tight")

    location_plot = df4[0:24].plot.barh(x='Word',y='Percentage')
    location_plot.invert_yaxis()
    location_plot.set_ylabel('Locations')
    location_plot.figure.savefig("{}/l_plot.png".format(company_name), dpi = 100, bbox_inches = "tight")
    
    plt.close('all')


# In[19]:


def export_activity():
    
    comment_count = []
    for i in post_comments:
        s = str(i).replace('comment','').replace('s','').replace(' ','')
        comment_count += [s]
    
    cleaned_dates = []
    for i in post_dates:
        d = str(i[0:3]).replace('\n\n', '').replace('•','').replace(' ', '')
        cleaned_dates += [d]
    
    data = {
        "Frequency": frequency,
        "Date Posted": cleaned_dates,
        "Media Type": media_types,
        "Post Text": post_texts,
        "Post Likes": post_likes,
        "Post Comments": comment_count,
        "Video Views": video_views,
        "Media Links": media_links
    }


    df = pd.DataFrame(data)

    writer = pd.ExcelWriter("{}/{}_activities.xlsx".format(company_name,company_name), engine='xlsxwriter')
    df.to_excel(writer, index =False)
    writer.save()


# In[20]:


def export_df():
    #Constructing Pandas Dataframe
    data = {
        "Gender": clean_list(user_gender),
        "Location": clean_list(liker_locations),
        "Age": est_ages,
        "Headline": liker_headlines,
        "Bio": user_bios,
        "Followed Influencers": clean_interests(influencers),
        "Followed Companies": clean_interests(companies)
    }

    df = pd.DataFrame(data)
    
    #Make backup data from to save our progress
    backup_data = {
        "Id": liker_names,
        "Gender": user_gender,
        "Location": liker_locations,
        "Age": est_ages,
        "Headline": liker_headlines,
        "Bio": user_bios,
        "Followed Influencers": influencers,
        "Followed Companies": companies    
    }
    
    backup_df = pd.DataFrame(backup_data)
    
    
    #Make a df of ages stats
    age_list = []
    for a in df["Age"]:
        if a != "unknown":
            age_list.append(int(a))
        else:
            pass
        
    age_data = {"Ages": age_list}    
    
    ages = pd.DataFrame(age_data)
    age_stats = ages.describe()
    age_stats = pd.DataFrame(age_stats)
    

    #Exporting csv to program folder for backup
    backup_df.to_csv("{}/{}_linkedin_backup.csv".format(company_name,company_name), encoding='utf-8', index=True)
    
    #Get data frames of interest counts
    common_companies, common_influencers, common_genders, common_locations = count_interests()
    
    try:
        #Plot the interest counts
        plot_interests(common_companies, common_influencers, common_genders, common_locations)

        time.sleep(1)

        #Create/Update Excel file
        writer = pd.ExcelWriter("{}/{}_linkedin.xlsx".format(company_name,company_name), engine='xlsxwriter')
        df.to_excel(writer, sheet_name='Users', index=False)
        common_companies.to_excel(writer, sheet_name='Company Interest', index=False)
        common_influencers.to_excel(writer, sheet_name='Influencer Interest', index=False)
        age_stats.to_excel(writer, sheet_name='Demographic Stats', index=True)
        writer.save()

        wb = load_workbook("{}/{}_linkedin.xlsx".format(company_name,company_name))

        #Adding plots to the sheets
        cws = wb["Company Interest"]
        c_img = openpyxl.drawing.image.Image('{}/c_plot.png'.format(company_name))
        c_img.anchor = 'H5'
        cws.add_image(c_img)

        iws = wb["Influencer Interest"]
        i_img = openpyxl.drawing.image.Image('{}/i_plot.png'.format(company_name))
        i_img.anchor = 'H5'
        iws.add_image(i_img)

        dws = wb["Demographic Stats"]
        g_img = openpyxl.drawing.image.Image('{}/g_plot.png'.format(company_name))
        g_img.anchor = 'D2'
        dws.add_image(g_img)
        l_img = openpyxl.drawing.image.Image('{}/l_plot.png'.format(company_name))
        l_img.anchor = 'B21'
        dws.add_image(l_img)

        #Save Excel file
        wb.save("{}/{}_linkedin.xlsx".format(company_name,company_name))
        
    except:
        pass
    
    #Keep Track of where we are in the foller list
    f= open("{}/{}_credentials.txt".format(company_name,company_name),"w+")
    f.write("username={}, password={}, page_index={}, page_url={}".format(username,password,page,page_url))
    f.close()
        
    #Export the Meta Data
    meta_data = {
    "Interest Pages": interest_pages,
    "Follower Counts": follower_counts,
    "Follow Rate": follow_rate
    }

    meta_df = pd.DataFrame(meta_data)

    meta_df.to_csv("meta_data.csv", encoding='utf-8', index=True)


# In[21]:


def get_source():  
    company_page = browser.page_source
    linkedin_soup = bs(company_page.encode("utf-8"), "html")
    #linkedin_soup.prettify()

    return linkedin_soup


# In[22]:


def scrape_activity():
    try:
        #activity_path = 'pv-profile-section__card-action-bar artdeco-container-card-action-bar artdeco-button artdeco-button--tertiary artdeco-button--3 artdeco-button--fluid  ember-view'
        activity_path = 'pv-profile-section__section-info'
        browser.find_element_by_xpath("//span[@class='{}']".format(activity_path)).click()
        time.sleep(1)
        print("clicked activity link")
        scroll()
        page_source = get_source()
        containers = page_source.findAll("div",{"class":"occludable-update ember-view"})
        time.sleep(2)
        
        #scape the activities and then close and switch back to main page
        for container in containers:
            try:
                scrape_post(container)
            except:
                break
         
        time.sleep(random.randint(1,2))
    except:
        return


# In[23]:



def scrape_users(links):
    
    for link in links:

        try:
            print("Clicking user")
            ActionChains(browser).key_down(Keys.SHIFT).key_down(Keys.COMMAND).click(link).key_up(Keys.SHIFT).key_up(Keys.COMMAND).perform()
            time.sleep(1)
            try:
                browser.switch_to.window(browser.window_handles[1])
            except:
                time.sleep(1)
                try:
                    button_path = 'fr artdeco-button artdeco-button--2 artdeco-button--primary ember-view'
                    browser.find_element_by_xpath("//button[@class='{}']".format(button_path)).click()
                    time.sleep(1)
                except:
                    browser.back()
                    time.sleep(1)
                continue
        
        
            time.sleep(2)

            #switch to post page and get source
            user_profile = get_source()
            time.sleep(2)

            #scape the post and then close and switch back to main page
            try:
                get_user_data(user_profile)
            except:
                pass
            
            try:
                button_path = 'artdeco-modal__dismiss artdeco-button artdeco-button--circle artdeco-button--muted artdeco-button--2 artdeco-button--tertiary ember-view'
                browser.find_element_by_xpath("//button[@class='{}']".format(button_path)).click()
                time.sleep()
            except:
                pass
                
            try:
                scroll_up()
                time.sleep(1)
                scrape_activity()
            except:
                pass
            
            time.sleep(1)
            browser.close()
            time.sleep(2)
            browser.switch_to.window(browser.window_handles[0])
            time.sleep(random.randint(1,2))
            
        except:
            pass

        


# In[24]:


def get_user_links():
    #scroll to end of list
    scroll()

    #find all post links
    path = "//span[@class='entity-result__title-text  t-16']"
    links = browser.find_elements_by_xpath(path)
    scroll_up()
    return links


# In[25]:


def current_time():
    current_time = datetime.now().strftime("%H:%M")
    return current_time


# In[26]:


def main():
    global page
    page_limit = 1000
    daily_count = 0
    skip_count = 0
    daily_limit = random.randint(2000,25000)
    
    while page < page_limit:

        links = get_user_links()
        scrape_users(links)
        export_df()
        export_activity()
        print("{} pages scraped so far".format(page))
        print(len(post_texts))
        
        
        #Stop if reached daily page view limit
        if daily_count >= daily_limit:
            print("Daily page limit of {} has been reached. Stopping for the day to prevent auto signout.".format(str(daily_limit)))
            while current_time() >= "01:00":
                schedule.run_pending()
                time.sleep(60)
            daily_count = 0

#         #Stop for the night
#         while current_time() < "07:05":
#             schedule.run_pending()
#             time.sleep(60)

        
        try:
            browser.find_element_by_xpath('//*[@class="artdeco-pagination__button artdeco-pagination__button--next artdeco-button artdeco-button--muted artdeco-button--icon-right artdeco-button--1 artdeco-button--tertiary ember-view"]').click()
            time.sleep(random.randint(1,5))
            page += 1
        except:
            print("All pages scraped")
            break   
        


# In[27]:


browser.switch_to.window(browser.window_handles[0])
if __name__ == '__main__':
    main()


# In[ ]:




