# git

**A distributed version control system**

---

- [git](#git)
  - [Install git](#install-git)
  - [What is a repository](#what-is-a-repository)
  - [Use git](#use-git)
  - [more advanced usage](#more-advanced-usage)
    - [branches](#branches)

**Yawei Liu**

*2021/11/26*

## Install git

* see [git](https://git-scm.com/downloads)

## What is a repository

A repository a.k.a. repo is nothing but a collection of source code, data file, note, and anything you want to put together.

## Use git

* tell git who you are

  * ```git config --global user.name "YOUR_USERNAME" ```
  * ```git config --global user.email "im_satoshi@musk.com"```
  * ```git config --global --list # To check the info you just provided```

* create a [github](https://github.com/) or [gitee](https://gitee.com/) account

  * you can put your repos in github or gitee, and then work/share with others.
  * you can find a lot of published repos in github and gitee and clone into your computer.

* clone a remote repo in [github](https://github.com/) or [gitee](https://gitee.com/)

  * find the address (can be seen when clicking the clone button, both **https** and **ssh** address are fine) of a remote repo in git [github](https://github.com/) or [gitee](https://gitee.com/). For example, 
    * lammps: https://github.com/lammps/lammps.git
    * ilmdtoolkit: https://gitee.com/yliu3803/ilmdtoolkit.git
  * in local terminal
    * ```cd some_folder_name```
    * ```git clone remote_repo_URL```

* recommended way to create a local repo and push to a remote repo in gitee

  * create a remote repo in git [github](https://github.com/) or [gitee](https://gitee.com/) (this is a recommended way to create your own repo because both [github](https://github.com/) and [gitee](https://gitee.com/) provide some guidlines to help you to set up your repo)
  * clone this repo to your local computer use the **ssh address** (can be seen when clicking clone button)
    * ilmdtoolkit: git@gitee.com:yliu3803/ilmdtoolkit.git
  * set up [ssh](https://linuxkamarada.com/en/2019/07/14/using-git-with-ssh-keys/#.YaF6-r3P0-Q) to enable your access to the remote repo from local computer
    * ```ssh-keygen -t rsa -C 'youremail@qq.com'```
    * copy the contents in ```~/.ssh/id_rsa.pub``` int your [gitee](https://gitee.com/) account settings
    * ```eval "$(ssh-agent -s)"``` #start the ssh-agent in background
    * ```ssh add  ~/.ssh/id_rsa``` #add your SSH private key to the ssh-agent
    * ```ssh-keygen -f ~/.ssh/id_rsa -p``` # reset passphrase

  * add/modify contents in your working directory (also the palce where your local repo is), [then](https://www.freecodecamp.org/news/learn-the-basics-of-git-in-under-10-minutes-da548267cc91/)
    * ```git add file_name``` add file(s) that is in the working directory to the staging area
    * ```git commit``` add all files that are staged to the local repository
    * ```git push``` add all committed files in the local repo to the remote repo
    * ```git fetch``` get files from the remote repository to the local repository but not into the working directory
    * ```git merge``` get the files from the local repository into the working directory
    * ```git pull``` equivalent to a ```git fetch``` followd by a ```git merge```.
    * tips: softwares such as [vscode](https://code.visualstudio.com/docs/editor/github) and [jupyterlab](https://github.com/jupyterlab/jupyterlab-git) have extensions that provide GUI to sync your local repo and remote repo and more advanced usage. 

## more advanced usage

### branches

<img title="git_branches" alt="git_branches" src="./images/git_branches_merge.png" width="300">

* ```git branch``` # check branches, branch with * is the current working one
* ```git branch branchname``` # create a new brance named as "branchname"
* ```git checkout branchname``` # switch to "branchname" branch
* ```git branch -d branchname``` # delete "branchname" branch
* ```git push origin branchname``` # push "branchname" branch to remote repo, ```origin``` is the the name of remote
* ```git push --set-upstream origin branchname``` # enable ```git push``` for "branchname" branch
* ```git push origin --delete branchname``` # delete "branchname" branch in remote repo
* merge one branch A to another branch B
  * ```git checkout branchB```
  * ```git merge brachA```



