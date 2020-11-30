# geeMigrator
> Method to facilitate migration of GEE assets from one account to another
* Recursively migrates all assets under a user-specified asset to another user-specified asset
* Handles migrating between two different accounts and:
  * Authentication to different accounts
  * Setting access control-list (ACL) permissions (who can read and write to a given asset folder/imageCollection)

## Primary POCs
* Ian Housman- ian.housman@usda.gov
* Leah Campbell- leah.campbell@usda.gov

## Dependencies
* Python 3
* earthengine-api

## Using
* Ensure you have Python 3 installed
  * <https://www.python.org/downloads/>
  
* Ensure the Google Earth Engine api is installed and up-to-date
  * `pip install earthengine-api --upgrade`
  * `conda update -c conda-forge earthengine-api`

* Clone or download this repository
  * Recommended: `git clone https://github.com/gee-community/geeMigrator`
  * If downloading, download .zip and unzip the file.

* Running script
  * Open `geeAssetMigratorExample.py` script and update the following variables:
    * Set the specified `sourceRoot` and `destinationRoot` to the asset level you would like to copy assets from and to (these must already exist)
      * E.g. if you would like to migrate all assets under a personal user account: `sourceRoot = 'users/fromUsername' and destinationRoot = 'users/toUsername'`
      * E.g. if you would like to migrate some assets under a personal user account: `sourceRoot = 'users/fromUsername/someFolder' and destinationRoot = 'users/toUsername/someFolder'`
      * E.g. if you would like to migrate some assets under a legacy project to a GCP project: `sourceRoot = 'projects/someProject/someFolder' and destinationRoot = 'projects/someGCPProject/someFolder'`
    * Updating the ACL permissions (who can read or write to a given asset folder or imageCollection). Source assets and destination assets can have their permissions updated. This is essential if the destination assets fall under a different account than the source assets. If this is the case, you must add the user, group, service account, or project as a writer to the source assets by listing it under the `sourceWriters` list.
      
      * E.g. `sourceWriters = ['user:destinationEmail@domain.com']`
  * The basic workflow within the script is:
    * `setupCredentialsForMigration` - Ensure tokens are available that have access to both the `sourceRoot` and `destinationRoot`
      * Tokens will be created if they do not exist by prompting the user to log into the appropriate account
      * The ee.Authenticate method will be used. This opens a login screen in your browser. You must log into the account that has access to the appropriate root folder, copy the token into the command prompt and press ENTER.
      * This process will run until a token can be found that has access to both the `sourceRoot` and `destinationRoot`. If this requires different tokens, it will automatically be handled.
    * `batchChangePermissions` - Add the destination account listed under `sourceWriters` to all assets under the `sourceRoot`
    * `copyAssetTree` - Copy all assets under the `sourceRoot` to the `destinationRoot` and update destination assets ACLs if specified under `changeDestinationPermissions`
    
    * DANGER!!!! Optional method to use is `deleteAssetTree`. This method will delete all assets under the specified asset level. This cannot be undone, but is useful for cleaning up any asset tree.
      * E.g. if `migrate.deleteAssetTree('users/fromUsername/someFolder')` is specified, all folders, imageCollections, images, and tables under `users/fromUsername/someFolder` will be deleted.
  * Run script 
