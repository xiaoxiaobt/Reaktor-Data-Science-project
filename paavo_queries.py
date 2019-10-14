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

