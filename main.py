from fastapi import FastAPI, UploadFile, File, Form
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os
from fastapi.responses import FileResponse
import shutil

from os.path import exists
import easyocr


app = FastAPI()
reader = easyocr.Reader(['en'], gpu=True) # this needs to run only once to load the model into memory
T1 = ()
counter=0

newlist= []
dobStringList = []
aadharStringList = []
gender = ""
dob =""
aadhaarNumber = ""
errorOccured = False
name = ""
aadharBackStringList = []
aadhaarBackNumber= ""
pincode = ""
gender_detection_incomplete = True 
aadhaar_detection_incomplete = True
aadhaar_back_detection_incomplete = True

dob_required = True
gov = "government of india"
pin_detection_incomplete =  True
secondlist =[]
successStack =[]
errorStack =[]
pan_detection_incomplete = True
panlist = []
pan =""


def gender_detection(y):
    global gender_detection_incomplete
    global gender

    if (y == "male" or "male" in y) and (gender_detection_incomplete ==True):
        gender = "male"
        gender_detection_incomplete = False
    elif (y == "female" or "male" in y)and (gender_detection_incomplete ==True):
        gender = "female"
        gender_detection_incomplete = False
    # for Transgenders, gender = "transgender"
    elif (y == "transgender" or "transgender" in y) and (gender_detection_incomplete ==True):
        gender = "transgender"
        gender_detection_incomplete = False
    # in case we fail to get the gender by ocr | gender = ""
    else:
        if gender_detection_incomplete:
            gender = ""
    

def generate_dob(y):
    global dob_required
    global newlist
    global dob

    if (dob_required ==True) and "dob" in y:
        dobStringList = y.split(": ",-1)
        newlist= newlist + dobStringList
        dob = dobStringList[1]
        dob_required = False
        print("dob ", dob)
       


                  

def generate_aadhaar(y) :
    global aadhaar_detection_incomplete
    global newlist
    global aadhaarNumber
              
    #12 digit adhaar with 2 spaces
    if (len(y) >=12 and len(y) <=15) and (aadhaar_detection_incomplete == True):
        print("y", y)
        aadharStringList= y.split()
        if aadharStringList[0].isdigit() & aadharStringList[1].isdigit() & aadharStringList[2].isdigit():
            aadhaarNumber= aadharStringList[0] + aadharStringList[1] + aadharStringList[2]
            newlist= newlist + aadharStringList
            aadhaar_detection_incomplete = not aadhaar_detection_incomplete
            print("front adhar numbr", aadhaarNumber)



def generate_backaadhaar(y):
    global aadhaar_back_detection_incomplete
    global aadhaarBackNumber
    global aadharBackStringList
    print("inside back adhar ok")
    if (len(y) >=12 and len(y) <=16)  and (aadhaar_back_detection_incomplete == True):
        aadharBackStringList= y.split()
        print(aadharBackStringList)
        print("in gen back", aadharBackStringList)
        if aadharBackStringList[0].isdigit() & aadharBackStringList[1].isdigit() & aadharBackStringList[2].isdigit():
            aadhaarBackNumber= aadharBackStringList[0] + aadharBackStringList[1] + aadharBackStringList[2]
            aadhaar_back_detection_incomplete = not aadhaar_back_detection_incomplete
          
            print("back adhar numbr", aadhaarBackNumber)



def generate_pincode(y):
    global pincode
    global pin_detection_incomplete
    if len(y) == 6  and (pin_detection_incomplete == True):
        pincode= y
        pin_detection_incomplete = not pin_detection_incomplete

def generate_pan(y):
    global pan
    global pan_detection_incomplete

    if len(y) == 10  and y[5:9].isdigit() and (pan_detection_incomplete == True):
        pan =y
        pan_detection_incomplete = False





@app.get("/")
def root():
    return{"Api is up and running"}

@app.post("/pan")
async def postpan(panNo: str =Form(...), fullName: str =Form(...),file: UploadFile = File(...)):
    global successStack
    global errorStack
    global pan_detection_incomplete
    global panlist
    global pan

    panlist = []
    successStack = []
    errorStack = []
    pan_detection_incomplete = True


    panNo= panNo.lower()
    fullName = fullName.lower()

    if file.filename.split(".",1)[0] == "pan":
        with open(f'{file.filename}', "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

            result = reader.readtext(file.filename)
            for (x,y,z) in result:
                y=y.lower()
                try:
                    generate_pan(y)
                    generate_dob(y)
                except:
                    errorOccured = True
                panlist.append(y)
            if "income tax department" in panlist or "govt of india" in panlist :
                if pan == panNo:
                    if fullName in newlist:
                        name = fullName
                        successStack.apend("Pan")
                else:
                    errorStack.append("Pan mismatched")
            else:
                errorStack.append("Text mismatched")
            print(panlist)

    if len(errorStack) == 0:
        return {"status": "success", "message": successStack} 
    else:
        return {"status": "failure", "message": errorStack}

#     income tax department
# govt of india
# permanent account number card

                

    

@app.post("/upload")
async def uploadFile(aadhaarNo: str =Form(...), fullName: str =Form(...),front: UploadFile= File(...), back: UploadFile= File(...)):
    global name
    global successStack
    global errorStack
    global aadhaar_detection_incomplete 
    global aadhaar_back_detection_incomplete 
    global secondlist
    global aadhaarBackNumber

    
    
    aadhaarNo= str(aadhaarNo)
    fullName = fullName.lower()
    print(aadhaarNo)
    print(fullName)
    # for img in files:

    aadhaar_detection_incomplete = True
    if front.filename.split(".",1)[0] == "front":
        with open(f'{front.filename}', "wb") as buffer:
            shutil.copyfileobj(front.file, buffer)

 
            result = reader.readtext(front.filename)
            for (x,y,z) in result:
                y=y.lower()
                try:
                    generate_dob(y)
                    generate_aadhaar(y)
                    gender_detection(y)
                except:
                    errorOccured = True
                newlist.append(y)

            if gov in newlist or gov.upper() in newlist:
                if (aadhaarNo[0:4] and aadhaarNo[4:8] and aadhaarNo[8:12])  in newlist:
                    if gender != "":
                        if fullName in newlist:
                            name = fullName
                            aadhaar_back_detection_incomplete = True
                            if back.filename.split(".",1)[0] == "back":
                                with open(f'{back.filename}', "wb") as buffer:
                                    shutil.copyfileobj(back.file, buffer)
                                    
                                    result = reader.readtext(back.filename)
                                    for (x,y,z) in result:
                                        y=y.lower()
                                        print("y", y)
                                        try:
                                            print("generating back adh")

                                            generate_backaadhaar(y)
                                          
                                            generate_pincode(y)
                                        except:
                                            errorOccured = True
                                        secondlist.append(y)
                                    print(secondlist)
                                    if pincode in secondlist:
                                        print("front aadhar", aadhaarNumber)
                                        print("back aadhar", aadhaarBackNumber)
                                        if aadhaarNumber == aadhaarBackNumber:
                                            successStack.append("Back")
                                        else:
                                            errorStack.append("Adhaar mismatch")

                                    else:
                                        errorStack.append("Pincode missing")
                                    print(secondlist)
                            else:
                                errorStack.append("Name not clearly detected")
                        else:
                            errorStack.append("GenderFail")
                            
                    else:
                        errorStack.append("AadhaarFail")
                else:
                    errorStack .append("GovFail")

            
            
            # if aadhaarNo[4:8] in newlist:
            #     print("yes for 2")
            # if aadhaarNo[8:12] in newlist:
            #     print("yes for 3")
            print(newlist)

    
                    
    if len(successStack) >= 1 and (len(errorStack)== 0):
        print(successStack)
        return {"status": "success", "message": successStack} 
    else:
        print(errorStack)
        return {"status": "success", "message": errorStack} 




    




# Step 1: extract dob, gender : 
# Step 2: Include aadhaar no 3 parts: xxxx, xxxx, xxxx
# Step 3: prepare some static front variables that should be there, and calculate the score. Score should be greater than full -2


#Sensible way:
# check if dob is consistent
# check if govt of india is there
# check if name and aadhar 4 digit set is in subset.

# save gender. (background)


#for tomorrow:
# save address
# save pincode
# compare father's name

# Aadhaar, UNIQUE IDERTIFICATION AUTHORITY OF INDIA, UNIQUE IDENTIFICATION AUTHORITY OF 
#  till 6 digit pincode , aadhaar no, 







