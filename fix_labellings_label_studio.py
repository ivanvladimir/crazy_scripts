from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Get the API key from the environment variable
API_KEY = os.getenv('API_KEY')

# Define the URL where Label Studio is accessible and the API key for your user account
LABEL_STUDIO_URL = 'https://doccano.iimas.unam.mx'

from label_studio_sdk.client import LabelStudio

# Connect to the Label Studio API and check the connection
ls = LabelStudio(base_url=LABEL_STUDIO_URL, api_key=API_KEY)

total=0
for item in  ls.tasks.list(project=6):
    path=item.data['audio'].split('/')
    if not len(path[5]) == 11:
        missing_directory=path[6][:11]
        print(missing_directory)
        corrected_path="/".join(path[0:5])+"/"+missing_directory+"/"+"/".join(path[6:])
        print(item.id)
        print(item.data['audio'])
        print(corrected_path)
        total+=1
        ls.tasks.update(id=item.id, data={"audio":corrected_path})
print(total)
