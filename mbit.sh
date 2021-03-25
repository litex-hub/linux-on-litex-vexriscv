source /opt/Xilinx/Vivado/2020.1/settings64.sh
rm -rf build/qmtech_wukong
./make.py \
--board=qmtech_wukong \
--cpu-count=4 \
<<<<<<< HEAD
--with-fpu \
--aes-instruction=True \
--video="1024x600@60Hz" \
--build
=======
--cpu-per-fpu=1 \
--with-fpu \
--aes-instruction \
--video=1920x1080@60Hz \
--build

>>>>>>> af014149a85bc810457e1bedc260d124777060ed
