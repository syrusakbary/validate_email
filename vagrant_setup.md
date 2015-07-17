How to Set Up Validate Email Using Vagrant on PC
-------------------------------------------------

1. Download Vagrant & Virtual Box
    * http://www.vagrantup.com/downloads
    * http://www.virtualbox.org/
2. Look at http://docs.vagrantup.com/v2/getting-started/ to make a linux virtual machine via vagrant
    * tl;dr using bash (Can use regular Windows Terminal)
        * Make a folder first, whenever you want to access the vm you will need to cd into that folder
        ```
        $ vagrant init hashicorp/precise32
        
        $ vagrant up
        
        $ vagrant ssh
        ```
        * This last command is used to go into your vm
3. Install pipin the vm
    * http://www.saltycrane.com/blog/2010/02/how-install-pip-ubuntu/
    * tl;dr
        * $ sudo apt-get install python-pip
4. Install pyDNS
    ```
    This is a package dependency of validate email

    $ sudo pip install pydns
    ```
5. Install git
   ```
    $ sudo apt-get install git
   ```
6. Clone the validate_email repo to your vm 
    * (Since its a new machine you will need to clone using the https url)
    * $ git clone git@github.com:efagerberg/validate_email.git
    * If you want to use your ssh keys on your machine you will need to add this line to the vagrant file under the config
        * Looks somthing like this:
          Vagrant::Config.run do |config|
          	# stuff
          	config.ssh.forward_agent = true
          end
7. cd into validate_email and run script
    ```
    $ cd validate_email

    $ python validate_email.py
    ```


