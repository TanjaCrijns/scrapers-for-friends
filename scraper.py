import requests
import math
import pickle
import time
from notify_run import Notify

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
        time.sleep(0.1)
        response = requests.post(
            url="https://www.woningnetregioutrecht.nl/webapi/zoeken/find/",
            data={"url": path, "command": "", "hideunits": "hideunits[]"},
        )
        for house in response.json()["Resultaten"]:
            if (any(city in house["PlaatsWijk"].lower() for city in cities)
                and int(house["Kamers"]) >= 2):
                houses.append(house)

    with open("houses.pkl", "rb") as fp:
        prev_houses = pickle.load(fp)

    messages = []
    for house in houses:
        if house not in prev_houses:
            house_url = (f"https://www.woningnetregioutrecht.nl{house['AdvertentieUrl']}")
            messages.append(f"Nieuw huis/appartement! {house_url}")

    with open("houses.pkl", "wb") as fp:
        pickle.dump(houses, fp)

    for message in messages:
        print(message)
        notify = Notify(endpoint="")
        notify.send(message)
