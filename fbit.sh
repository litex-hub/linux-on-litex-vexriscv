source /opt/Xilinx/Vivado/2020.1/settings64.sh
./make.py \
--board=qmtech_wukong \
--cpu-count=4 \
--cpu-per-fpu=1 \
--with-fpu \
--aes-instruction \
--video=1920x1080@60Hz \
--flash

