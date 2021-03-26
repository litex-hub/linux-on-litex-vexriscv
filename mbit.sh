source /opt/Xilinx/Vivado/2020.1/settings64.sh
rm -rf build/qmtech_wukong
./make.py \
--board=qmtech_wukong \
--cpu-count=4 \
--cpu-per-fpu=1 \
--with-fpu \
--aes-instruction=true \
--video=1920x1080@60Hz \
--build

