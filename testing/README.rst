================================
widgetastic.patternfly-Testing
================================
This project uses standard pattern seen across different python projects for testing.

We use Travis CI to run unit tests against submitted PRs. Travis uses Tox(like python3-tox pacakage)
to run the unit tests.

There is no requirements.txt as this project uses tox.ini to keep to requirements and run the tests.

* To run the unit tests:
	- Make sure you are in projects root directory where tox.ini is located
	- Have a virtualenv created and activated
	- Install the relevant tox package
	- Run the command:
		`tox -e py36`
		(replace it with appropriate python version, supported options are py27, py34, py35, py36, py37)
* Browser Config:
	- Make sure you have FF installed on your system and latest "geckodriver" is in your PATH.
	  It can be downloaded from https://github.com/mozilla/geckodriver/
	- testing/conftest.py: This file contains basic config for selenium and browser. It has an `options.headless = True`
	  which makes the text execution run in an headless browser. If you want to see the browser window you need to remove
	  this option or change it to False.(This is a tip for new contributors only)
* testing_page.html:
	- This is a page which contains elements that are required for unit tests.
	- pytest-localserver package makes httpserver fixture available, which would serve the testing_page.html over localhost address.
	- With the help of that, tox would load page in the browser and run the tests.
	- If you have a new widget written for an element that is not part of testing_page.html then you may need to add it. Please
	  refer Patternfly for the same(https://www.patternfly.org/pattern-library/)
