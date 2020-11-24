import geeAssetMigratorLib as migrate
###################################################################################################
# This script recursively migrates Google Earth Engine assets from one repository to a new one, sets permissions, and deletes old assets if needed.
###################################################################################################
"""
   Copyright 2019 Ian Housman and Leah Campbell

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""
###################################################################################################
###################################################################################################
#Set up tokens for migrating
#The method assumes you are migrating assets from one account to another and sets up two different credentials to take care of 
#any permission conflicts
#Specify the directory to store the tokens
token_dir = 'c:/tokens'

# Repository you are moving from:
sourceRoot = 'users/iwhousman/test'


# Repository you are moving to:
destinationRoot = 'users/usfs-ihousman/migrationTest'


# If the credential you're using does not have editor permissions in the source repository
# Must include 'user:' prefix if it is a individual's Email or 'group:' if it is a Google Group

sourceReaders = []
sourceWriters = ['user:ian.housman@usda.gov']
source_all_users_can_read = False

#Optionally, update the permissions of the copied destination assets
changeDestinationPermissions = True
destinationReaders = []
destinationWriters = ['user:iwhousman@gmail.com']
destination_all_users_can_read = False
###################################################################################################
#Step 1: set up credentials for the source and destination
source_token, destination_token = migrate.setupCredentialsForMigration(token_dir,sourceRoot,destinationRoot,overwrite = False)

#Step 2: Initialize GEE using the source token and update permissions on the source folder
migrate.initializeFromToken(source_token)
migrate.batchChangePermissions(None, sourceRoot,sourceReaders,sourceWriters, source_all_users_can_read)

#Step 3: Initialize GEE using the destination token and copy folders
migrate.initializeFromToken(destination_token)
migrate.copyAssetTree(sourceRoot,destinationRoot,changeDestinationPermissions,destinationReaders,destinationWriters,destination_all_users_can_read)
# ###################################################################################################
###################################################################################################
###################################################################################################
# !!!!!!!!!!!! DANGER !!!!!!!!!!!!
# !!!!!!!!!!!! DANGER !!!!!!!!!!!!
# !!!!!!!!!!!! DANGER !!!!!!!!!!!!
# !!!!!!!!!!!! DANGER !!!!!!!!!!!!
#Delete folder tree if you would like to clean up any asset trees
#migrate.deleteAssetTree(sourceRoot)

        
