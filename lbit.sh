source /opt/Xilinx/Vivado/2020.1/settings64.sh
./make.py \
--board=qmtech_wukong \
--cpu-count=4 \
--with-fpu \
--aes-instruction=True \
--video="1024x600@60Hz" \
--load
