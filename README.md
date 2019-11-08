# sc2_lib
This library is used to enhance original package [sc2](https://github.com/Dentosal/python-sc2/tree/develop). Please note that the master brance of sc2 is no longer working, althrough some [minor fix](https://github.com/Dentosal/python-sc2/issues/283#issuecomment-508407630) will solve the problems. I recommand using bug free develop version instead, so you don't have to change anything in the source code. If you don't have sc2 installed, please run 
```
pip3 install -e git+https://github.com/Dentosal/python-sc2.git@develop#egg=sc2
```
in your command prompt on Windows 10 to install the develop branch of sc2. Then you can run
```
pip3 install -e git+https://github.com/derpypony/sc2_lib.git#egg=sc2_lib
```
to install this library.

The main functions in this library include [distribute_workers](sc2_lib/distribute_workers.py#L13) from distribute_workers.py, which is used to replace the original [distribute_workers](https://github.com/Dentosal/python-sc2/blob/84b1231eab91320204c146bd5682bb2a1b5f23cf/sc2/bot_ai.py#L293)
