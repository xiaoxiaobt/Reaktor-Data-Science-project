surface_population_query = {
  "query": [
    {
      "code": "Tiedot",
      "selection": {
        "filter": "item",
        "values": [
          "Pinta_ala",
          "He_vakiy"
        ]
      }
    }
  ],
  "response": {
    "format": "csv"
  }
}

population_query = {
  "query": [
    {
      "code": "Tiedot",
      "selection": {
        "filter": "item",
        "values": [
          "He_vakiy"
        ]
      }
    }
  ],
  "response": {
    "format": "json-stat"
  }
}

full_query = {
  "query": [],
  "response": {
    "format": "csv"
  }
}
# url and query for paavo housing data
housing_url = 'http://pxnet2.stat.fi/PXWeb/api/v1/en/StatFin_Passiivi/asu/ashi/statfinpas_ashi_pxt_004_2017q4.px'

housing_query = {
  "query": [
    {
      "code": "Neljännes",
      "selection": {
        "filter": "item",
        "values": [
          "0"
        ]
      }
    },
    {
      "code": "Talotyyppi",
      "selection": {
        "filter": "item",
        "values": [
          "6"
        ]
      }
    },
    {
      "code": "Rakennusvuosi",
      "selection": {
        "filter": "item",
        "values": [
          "8"
        ]
      }
    },
  ],
  "response": {
    "format": "csv"
  }
}

ts_housing_query = {
  "query": [
    {
      "code": "Talotyyppi",
      "selection": {
        "filter": "item",
        "values": [
          "6"
        ]
      }
    },
    {
      "code": "Rakennusvuosi",
      "selection": {
        "filter": "item",
        "values": [
          "8"
        ]
      }
    }
  ],
  "response": {
    "format": "csv"
  }
}
