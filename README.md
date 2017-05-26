# OpenAPI Documentation Generator

## Setup
### Installation
First, setup a virtual environment:
```sh
[doc-scraper]$ pip install virtualenv
[doc-scraper]$ virtualenv openapidocs
[doc-scraper]$ source openapidocs/bin/activate
```
Install dependencies with `pypi`:
```sh
[doc-scraper]$ pip install -r requirements.txt
```

Clone `github.okta.io` into the directory:
```sh
[doc-scraper]$ git clone git@github.com:okta/okta.github.io.git
[doc-scraper]$ git pull origin weekly/jm-fix-closing-tags
```
*Note* This branch will be merged into master by end of May

### Generate Docs
The following script will parse through the included `okta.github.io` repository looking for the documented API endpoints.

```sh
[doc-scraper]$ python scraper.py
```

To remove old directories, use the `clean` argument:
```sh
[doc-scraper]$ python scraper.py clean
```

Once completed, you will have a directory tree similar to below:
```
openapidocs
|- api-v1-users
	|- GET
		|- description.md
		|- schema.json
	|- POST
		|- examples
			|- Create-User-in-Group
				|- description.md
				|- example.json
			|- Create-User-with-Password
				|- description.md
				|- example.json			
		|- description.md
		|- schema.json
	...

```

| Filename        | Description                                                                         | 
| --------------- | ----------------------------------------------------------------------------------- | 
| `description.md`| Summary of the API call or example                                                  |
| `schema.json`   | Lists in JSON format the known parameters, release_cycle, and title of the API call |
| `example.json`  | Request example in JSON format of the API call                                      |

