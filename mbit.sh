source /opt/Xilinx/Vivado/2020.1/settings64.sh
rm -rf build/qmtech_wukong
./make.py \
--board=qmtech_wukong \
--cpu-count=4 \
--with-fpu \
--aes-instruction=True \
--video="1024x600@60Hz" \
--build
