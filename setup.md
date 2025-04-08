clone repo to your workspace
open .azureml folder
change the name of config1.json to config.json
put your credentials in the config.json

create a .env file with the following credentials
        path_to_src="local/path/to/the/src"
        maps_key="api_key_to_the_azure_maps"
        X-Master-Key= "api_key_to__json_bin"
        X-Access-Key= "api_key_to_json_collection"

for initial training
     run upload_configs.py
     run the submit_training.py

from submit training you will get models in azureml studio  workspace

download the model of your choice

save the model to saved models

to load model
      go to loading.py , ensure model_path points to your downloaded model
      then run submit_model.py


in the azureml studio you can follow the submitted jobs and various metrics such as reward vs step


