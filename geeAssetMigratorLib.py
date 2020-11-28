import ee,os,json,re,shutil,ctypes,glob,secrets
from google.oauth2.credentials import Credentials
###################################################################################################
"""
   Copyright 2020 Ian Housman and Leah Campbell

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
#Library of functions for recursively migrating Google Earth Engine assets from one repository to a new one, sets permissions, and deletes old assets if needed.
###################################################################################################
def check_end(in_path, add = '/'):
    if in_path[-len(add):] != add:
        out = in_path + add
    else:
        out = in_path
    return out
###################################################################################################
#Function to authenticate to a user account and create a custom token at a specified path
#If there is an existing token, it will be retained in the default .config location
#Optionally, this token can be used to initialize GEE
def custom_authenticate(token_path_name,initialize = True,overwrite = False):
    token_path_name = os.path.normpath(token_path_name)
    #Ensure token directory exists
    if os.path.exists(os.path.dirname(token_path_name)) == False:os.makedirs(os.path.dirname(token_path_name))

    #If the token doesn't already exist or overwrite == True, create it
    if os.path.exists(token_path_name) == False or overwrite:

        #Rename any existing credentials
        existing_credentials_moved = False
        if os.path.exists(ee.oauth.get_credentials_path()):
          shutil.move(ee.oauth.get_credentials_path(),ee.oauth.get_credentials_path()+'_temp')
          existing_credentials_moved = True

        #Get new credentials and move them to the specified location
        ee.Authenticate()
        default_token = ee.oauth.get_credentials_path()
        shutil.move(default_token,token_path_name)

        #Rename the existing credentials back to the default
        if existing_credentials_moved:
          shutil.move(ee.oauth.get_credentials_path()+'_temp',ee.oauth.get_credentials_path())

    #Initialize using the credentials if chosen
    if initialize:
        initializeFromToken(token_path_name)
###################################################################################################
#Function to add a list of root assets for a given GEE token file
#Stores the paths in the same json as the token
def addRoots(token_path_name):
    print('Adding root paths to:', token_path_name)
    
    initializeFromToken(token_path_name)
    available_roots = [i['id'] for i in ee.data.getAssetRoots()]

    token = json.load(open(token_path_name))
    token['roots'] = available_roots
    # print(available_roots,token)
    o = open(token_path_name,'w')
    o.write(json.dumps(token))
    o.close()
###################################################################################################
#Function to initialize from specified token
#Does not un-initialize any existing initializations, but will point to this set of credentials    
def initializeFromToken(token_path_name):
    print('Initializing GEE using:',token_path_name)
    refresh_token = json.load(open(token_path_name))['refresh_token']
    c = Credentials(
          None,
          refresh_token=refresh_token,
          token_uri=ee.oauth.TOKEN_URI,
          client_id=ee.oauth.CLIENT_ID,
          client_secret=ee.oauth.CLIENT_SECRET,
          scopes=ee.oauth.SCOPES)
    ee.Initialize(c)
###################################################################################################
#Function to set up a new token and check if it works for specified root
def setupToken(token_dir,root,overwrite = False,name = ''):
    if not token_dir:token_dir = os.path.dirname(ee.oauth.get_credentials_path())
    token_dir = check_end(token_dir)
    root = fixAssetPath(root)
    token = token_dir+'credentials_'+secrets.token_urlsafe(32) # '_'.join(root.split('/'))
        
    if os.path.exists(token) == False or overwrite:
        a = ctypes.windll.user32.MessageBoxW(0, 'Please authenticate to the account that has access to the "{}" asset folder.\n\nMake sure you select the account that has owner level permissions for the asset folder you are copying from.\n\nSometimes the authentication URL will open in a browser instance that does not immediately list the account. You can copy and paste the URL into another browser instance if needed.\n\nThe token will be stored as "{}"'.format(root,token), "!!!! IMPORTANT !!!! Set up {}token".format(name+ ' '), 1)
        if a == 1:
            custom_authenticate(token,initialize = False,overwrite = overwrite)
            addRoots(token)
    return token
###################################################################################################
#Function to set up credentials that have access to a specified asset root folder
#This function will run until it can find a token that has the root listed under the available assetRoots
def smartGetCredentials(root, token_dir = os.path.dirname(ee.oauth.get_credentials_path()),overwrite = False,name = ''):
    if not token_dir:token_dir = os.path.dirname(ee.oauth.get_credentials_path())
    #House keeping
    if os.path.exists(token_dir) == False:os.makedirs(token_dir)
    token_dir = check_end(token_dir)
    root = fixAssetPath(root)
    
    #Try to find a token with asset roots
    #Asset roots will be added to token json if they are not already there 
    can_write = False
    iteration = 1
    while not can_write:
        #List available tokens (assumes only token files are in token_dir)
        os.chdir(token_dir)
        tokens = glob.glob('*')

        #Find tokens that contain the root as an available asset root
        for token in tokens:
            can_write = canWrite(token,root)
          
            if can_write:
                out_token = token
                break
        #If no available tokens have access to the root, set up a new one
        if not can_write:
            if iteration > 1:
                ctypes.windll.user32.MessageBoxW(0, 'The account you just authenticated to does not have access to {}. Please retry and ensure you select an account that does have access to {}.'.format(root,root), "!!!! IMPORTANT !!!! Set up {}token failed. RETRY!".format(name+ ' '), 1)
        
            out_token = setupToken(token_dir,root,overwrite = overwrite,name = name)
            iteration += 1

    # ctypes.windll.user32.MessageBoxW(0, 'Successfully found token that has access to {}'.format(root), "!!!! SUCCESS !!!!", 1)
    print('Successfully found token that has access to {}'.format(root))
    return out_token
##################################################################################################
#Get root dir of an asset
def getAssetRoot(asset):
    return re.search("^projects/[^/]+/assets/", asset).group(0)
###################################################################################################
#See if a given token path can access a specified asset root
def canWrite(token,root):

    #House keeping
    root = check_end(root)
    root = fixAssetPath(root)
    
    #See if there are stored roots in json
    can_write = False
    token_dict = json.load(open(token))
    print('roots' not in token_dict.keys())

    #First try to add the owner roots and see if that is listed
    if 'roots' not in token_dict.keys():
        addRoots(token)
        token_dict = json.load(open(token))
    root_matches = [i for i in token_dict['roots'] if root.find(i) == 0]
    if root_matches != []:can_write = True

    #If root is still not listed for token, try seeing if the asset root quota can be acquired
    if not can_write:
        try:
            initializeFromToken(token)
            quota = ee.data.getAssetRootQuota(getAssetRoot(root))
            can_write = True
            
            #Cache it if it has access
            token_dict['roots'].append(root)
            o = open(token,'w')
            o.write(json.dumps(token_dict))
            o.close()
        except Exception as e:
            print('Token {} cannot access {}'.format(token,root))
            
    return can_write
###################################################################################################
#Function to get credentials set up for two accounts for asset migration
def setupCredentialsForMigration(token_dir,sourceRoot,destinationRoot,overwrite = False):
    #Get tokens
    source_token = smartGetCredentials(sourceRoot, token_dir,overwrite = overwrite,name = 'Source')
    destination_token = smartGetCredentials(destinationRoot, token_dir,overwrite = overwrite,name = 'Destination')
    return source_token, destination_token
# ###################################################################################################
def fixAssetPath(path,legacy_prefix = 'projects/earthengine-legacy/assets/',regex = "^projects/[^/]+/assets/.*$"):
    if re.match(regex,path) == None:
        path = legacy_prefix + path
    return path
###################################################################################################
#Function to get all folders, imageCollections, images, and tables under a given folder or imageCollection level
def getTree(fromRoot,toRoot,treeList = None):
    pathPrefix = 'projects/earthengine-legacy/assets/'

    #Handle inconsistencies with the earthengine-legacy prefix
    fromRoot = fixAssetPath(fromRoot)
    toRoot = fixAssetPath(toRoot)

    #Initialize treeList with original root directories if None
    if treeList == None: 
        try:
            rootType = ee.data.getAsset(fromRoot)['type']
        except:
            rootType = 'FOLDER'

        treeList = [[rootType,fromRoot,toRoot]]

    #Clean up the given paths
    if(fromRoot[-1] != '/'):fromRoot += '/'
    if(toRoot[-1] != '/'):toRoot += '/'

    

    # print(fromRoot,toRoot,treeList)
    #List assets 
    assets = ee.data.listAssets({'parent':fromRoot})['assets']


    #Reursively walk down the tree
    nextLevels = []
    for asset in assets:
        fromID = asset['name']
        fromType = asset['type']
        toID = fromID.replace(fromRoot,toRoot)
        
        if fromType in ['FOLDER','IMAGE_COLLECTION']:
            nextLevels.append([fromID,toID])
        treeList.append([fromType,fromID,toID])  
    
    
    for i1,i2 in nextLevels:
        getTree(i1,i2,treeList)
    return treeList
###################################################################################################
#Function for setting permissions for all files under a specified root level
#Either a list of assets a root to start from can be provided
def batchChangePermissions(assetList = None,root = None,readers = [],writers = [], all_users_can_read = False):
    if assetList == None:
        assetList = [i[1] for i in getTree(root,root)]

    for assetID in assetList:
        print('Changing permissions for: {}'.format(assetID))
        try:
            ee.data.setAssetAcl(assetID, json.dumps({u'writers': writers, u'all_users_can_read': all_users_can_read, u'readers': readers}))
        except Exception as e:
            print(e)
###################################################################################################
#Function to copy all folders, imageCollections, images, and tables under a given folder or imageCollection level
#Permissions can also be set here 
def copyAssetTree(fromRoot,toRoot,changePermissions = False,readers = [],writers = [],all_users_can_read = False):
    print('Getting asset tree list')
    treeList = getTree(fromRoot,toRoot)
  
    #Iterate across all assets and copy and create when appropriate
    for fromType,fromID,toID in treeList:
        if fromType in ['FOLDER','IMAGE_COLLECTION']:
            try:
                print('Creating {}: {}'.format(fromType,toID))
                ee.data.createAsset({'type':fromType, 'name': toID})
            except Exception as e:
                print(e)
        else:
            try:
                print('Copying {}: {}'.format(fromType,toID))
                ee.data.copyAsset(fromID,toID,False)

            except Exception as e:
                print(e)
        print()
        print()

    if changePermissions:
        batchChangePermissions(assetList = [i[2] for i in treeList],root = None,readers = readers,writers = writers, all_users_can_read = all_users_can_read)
###################################################################################################
#Function to delete all folders, imageCollections, images, and tables under a given folder or imageCollection level
def deleteAssetTree(root):
    answer = input('Are you sure you want to delete all assets under {}? (y = yes, n = no): '.format(root))
    print(answer)
    if answer.lower() == 'y':
        answer = input('You answered yes. Just double checking. Are you really sure you want to delete all assets under {}? (y = yes, n = no): '.format(root))
        if answer.lower() == 'y':
            treeList = getTree(root,root)[1:]
            treeList.reverse()
            for fromType, ID1,ID2 in treeList:
                print('Deleting {}'.format(ID1))
                try:
                    ee.data.deleteAsset(ID1)
                except Exception as e:
                    print(e)
