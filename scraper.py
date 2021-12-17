import requests
import math
import time
import boto3
import json

def telegram_bot_sendtext(bot_message):
    bot_token = ''
    bot_chatID = ''
    send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + bot_chatID + '&parse_mode=Markdown&text=' + bot_message
    response = requests.get(send_text)
    return response.json()

def lambda_handler(event, context):
    url = "https://www.woningnetregioutrecht.nl/webapi/zoeken/find/"

    response = requests.post(
        url=url,
        data={"url": "model[Regulier%20aanbod]",
            "command": "",
            "hideunits": "hideunits[]",},).json()
    paths = ["model[Regulier%20aanbod]", "model[Vrijesectorhuur]", "model[Loting]"]
    filter_counts = response["Filters"]["FiltersList"][0]["OptieLijst"]["Opties"]
    for count in filter_counts:
        if count["Value"] == "Regulier aanbod":
            n_reg_aanbod = count["Aantal"]
            if n_reg_aanbod > 10:
                for i in range(1, math.ceil(n_reg_aanbod / 10) + 1):
                    paths.append(f"model[Regulier%%20aanbod]~page[{i}]")
        if count["Value"] == "Loting":
            n_loting = count["Aantal"]
            if n_loting > 10:
                for i in range(1, math.ceil(n_loting / 10) + 1):
                    paths.append(f"model[Loting]~page[{i}]")
        if count["Value"] == "Vrijesectorhuur":
            n_vrij_sec = count["Aantal"]
            if n_vrij_sec > 10:
                for i in range(1, math.ceil(n_vrij_sec / 10) + 1):
                    paths.append(f"model[Vrijesectorhuur]~page[{i}]")

    cities = [
        "utrecht",
        "groenekan",
        "bilthoven",
        "de bilt",
        "vleuten",
        "de meern",
        "bilt",
        "meern",
        "nieuwegein",
        "bunnik",
        "houten",
        "maarssen",
    ]
    houses = []
    for path in paths:
        time.sleep(0.5)
        response = requests.post(
            url="https://www.woningnetregioutrecht.nl/webapi/zoeken/find/",
            data={"url": path, "command": "", "hideunits": "hideunits[]"},
        )
        for house in response.json()["Resultaten"]:
            if (any(city in house["PlaatsWijk"].lower() for city in cities) and int(house["Kamers"]) >= 2):
                keys = ["Adres", "PlaatsWijk", "Kamers", "PublicatieId", "AdvertentieUrl"]
                temp_house = {key: house[key] for key in keys}
                houses.append(temp_house)

    s3 = boto3.resource('s3')
    bucket = "woningnet"
    file = "houses.json"
    prev_houses = json.loads(s3.Bucket(bucket).Object("houses.json").get()['Body'].read().decode('utf-8'))

    messages = []
    for house in houses:
        if house not in prev_houses:
            house_url = (f"https://www.woningnetregioutrecht.nl{house['AdvertentieUrl']}")
            adres, plaats, kamers = house["Adres"], house["PlaatsWijk"], house["Kamers"]
            messages.append(f"{adres}, {plaats}, {kamers} kamers: \n{house_url}")
    
    for message in messages:
        print(message)
        test = telegram_bot_sendtext(message)

    new_houses = prev_houses + [house for house in houses if house not in prev_houses]
    s3.Object(bucket, file).put(Body=(bytes(json.dumps(new_houses).encode('UTF-8'))))