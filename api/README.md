Run the api manually (gets around Windows localhost issue):
- `cd api`
- `pip install -r requirements.txt`
- `uvicorn main:app --reload`

Run the api in docker:
- `cd api`
- `docker build -t api .`
- `docker run -p 8000:8000 api`