cd $HOME
git clone git@github.com:linuxcnc-probe-screen/probe-screen-ng.git

cd $HOME/linuxccnc/configs/MyConfigName

ln -s $HOME/probe-screen-ng/macros macros-psng

ln -s $HOME/probe-screen-ng/psng psng

ln -s $HOME/probe-screen-ng/python python

# to change branch
git checkout files_cleanup
