source /opt/Xilinx/Vivado/2020.1/settings64.sh
./make.py \
--board=qmtech_wukong \
--cpu-count=4 \
<<<<<<< HEAD
--with-fpu \
--aes-instruction=True \
--video="1024x600@60Hz" \
--flash
=======
--cpu-per-fpu=1 \
--with-fpu \
--aes-instruction \
--video=1920x1080@60Hz \
--flash

>>>>>>> af014149a85bc810457e1bedc260d124777060ed
