source /opt/Xilinx/Vivado/2020.1/settings64.sh
rm -rf build/qmtech_wukong
./make.py --board=qmtech_wukong --with-fpu --video=1920x1080@60Hz --build

