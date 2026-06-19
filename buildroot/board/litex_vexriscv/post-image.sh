#!/bin/bash

set -e

BOARD_DIR="$(dirname $0)"
GENIMAGE_CFG="${BOARD_DIR}/genimage.cfg"
GENIMAGE_TMP="${BUILD_DIR}/genimage.tmp"

LINUX_ON_VEXRISCV_OUT_DIR=$BR2_EXTERNAL_LITEX_VEXRISCV_PATH/../images
DST_DTB=$LINUX_ON_VEXRISCV_OUT_DIR/rv32.dtb
DST_OPENSBI=$LINUX_ON_VEXRISCV_OUT_DIR/opensbi.bin
DST_IMAGE=$LINUX_ON_VEXRISCV_OUT_DIR/Image
DST_ROOTFS_CPIO=$LINUX_ON_VEXRISCV_OUT_DIR/rootfs.cpio
DST_ROOTFS_CPIO_GZ=$LINUX_ON_VEXRISCV_OUT_DIR/rootfs.cpio.gz
DST_ROOTFS_EXT4=$LINUX_ON_VEXRISCV_OUT_DIR/rootfs.ext4

rm -f $DST_OPENSBI $DST_ROOTFS_CPIO $DST_ROOTFS_CPIO_GZ $DST_ROOTFS_EXT4 $DST_IMAGE
ln -s $BINARIES_DIR/fw_jump.bin $DST_OPENSBI
ln -s $BINARIES_DIR/Image $DST_IMAGE
ln -s $BINARIES_DIR/rootfs.cpio $DST_ROOTFS_CPIO
if [ -e $BINARIES_DIR/rootfs.cpio.gz ]; then
	ln -s $BINARIES_DIR/rootfs.cpio.gz $DST_ROOTFS_CPIO_GZ
else
	gzip -c $BINARIES_DIR/rootfs.cpio > $DST_ROOTFS_CPIO_GZ
fi
ln -s $BINARIES_DIR/rootfs.ext4 $DST_ROOTFS_EXT4

if [ ! -e $DST_DTB ]; then
	echo ""
	echo "Warning: missing file $DST_DTB"
	echo "a dummy file will be created"
	echo "must be replaced manually by required rv32.dtb"
	echo ""
	touch $DST_OPENSBI
fi

if [ -e $DST_DTB ]; then
	DTB_DTS=${GENIMAGE_TMP}/rv32.dts
	dtc -I dtb -O dts -o $DTB_DTS $DST_DTB
	INITRD_START=$(sed -n -E 's/.*linux,initrd-start[[:space:]]*=[[:space:]]*<([^>]+)>.*/\1/p' $DTB_DTS | head -n 1)
	if [ -n "$INITRD_START" ]; then
		INITRD_SIZE=$(stat -c%s $DST_ROOTFS_CPIO_GZ)
		INITRD_END=$(printf "0x%x" $((INITRD_START + INITRD_SIZE)))
		sed -i -E "s/(linux,initrd-end[[:space:]]*=[[:space:]]*<)0x[0-9a-fA-F]+(>)/\1${INITRD_END}\2/" $DTB_DTS
		dtc -I dts -O dtb -o $DST_DTB $DTB_DTS
	fi
fi

# Pass an empty rootpath. genimage makes a full copy of the given rootpath to
# ${GENIMAGE_TMP}/root so passing TARGET_DIR would be a waste of time and disk
# space. We don't rely on genimage to build the rootfs image, just to insert a
# pre-built one in the disk image.

trap 'rm -rf "${ROOTPATH_TMP}"' EXIT
ROOTPATH_TMP="$(mktemp -d)"

rm -rf "${GENIMAGE_TMP}"

genimage \
    --rootpath "${ROOTPATH_TMP}"   \
    --tmppath "${GENIMAGE_TMP}"    \
    --inputpath "${LINUX_ON_VEXRISCV_OUT_DIR}"  \
    --outputpath "${LINUX_ON_VEXRISCV_OUT_DIR}" \
    --config "${GENIMAGE_CFG}"

exit $?
