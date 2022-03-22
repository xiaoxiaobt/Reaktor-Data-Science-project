# Data Science project - Reaktor

## Table of Contents

- [General information](#general-information)
- [Screenshots](#screenshots)
- [Installation](#installation)
- [Usage](#usage)
- [Test](#tests)
- [Privacy](#privacy)
- [Team](#team)
- [Credits](#credits)
- [License](#license)

---

## General information

Kodimpi is a web application that provides suggestions for relocation in Finland through data-driven approaches. After users input their income, age, current location, occupation, household size, as well as their preference of relocation, near or far away from their current one, the recommendation system provides a recommendation of the best place to relocate. Alternatively, users can also interact with the map to find out some key insights about the location.

## Screenshots

![Navigation](assets/screenshots/navigation.png)
![Recommendation](assets/screenshots/prediction.png)

## Installation

The service can be directly accessed from <https://kodimpi.herokuapp.com/>.

To run the application on a local machine, follow steps below:

### Prerequisites

- Python 3.6+
- git

### Clone

- Clone this repo to your local machine using

```shell
git clone https://github.com/xiaoxiaobt/Reaktor-Data-Science-project.git
```

### Setup

- Go to the project directory by using

```shell
cd Reaktor-Data-Science-project
```

> update and install dependencies

```shell
pip install -r requirements.txt
```

> run the application

```shell
python app.py
```

Now the application can be accessed from <http://127.0.0.1:8050/>

---

## Usage

- Start the application, and enter the required data into the left panel. Then, click `Estimate` to see your recommendation.
- Alternatively, explore the map with the mouse and click on one area that is interesting for you.

---

## Tests

Unit tests have being implemented to make sure the dataframe has the correct attributes and shape.

---

## Privacy

**We care about your privacy**. We take your data privacy seriously, as we always have.

We need to collect and treat your personal data to provide you a precise suggestion for relocation. All data will not be stored on our server.
This service fully complies with the EU General Data Protection Regulation (GDPR).
The full source code of the service can be found from [here](https://github.com/xiaoxiaobt/Reaktor-Data-Science-project).

---

## Team

| **Letizia** | **Taige** | **Roope** | **Trang** | **Thong** |
| :---: |:---:| :---:| :---:| :---:|
| [![Letizia](https://avatars1.githubusercontent.com/u/45148109?s=200&v=4)](https://github.com/letiziaia)    | [![Taige](https://avatars2.githubusercontent.com/u/16875716?s=200&v=4)](https://github.com/xiaoxiaobt) | [![Roope](https://avatars2.githubusercontent.com/u/43811718?s=200&v=4)](https://github.com/rooperuu)  |[![Trang](https://avatars3.githubusercontent.com/u/55182434?s=200&v=4)](https://github.com/trangmng) | [![Thong](https://avatars0.githubusercontent.com/u/32213097?s=200&v=4)](https://github.com/trananhthong)  |

---

## Credits

The project was supervised by Jorma Laaksonen from Aalto University and Jaakko Särelä from Reaktor.

---

## License

- **[MIT license](https://opensource.org/licenses/mit-license.php)**
- Copyright 2019 © Letizia, Taige, Roope, Trang, Thong
