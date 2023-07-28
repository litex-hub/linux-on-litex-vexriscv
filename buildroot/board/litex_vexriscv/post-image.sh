#!/bin/bash

set -e

BOARD_DIR="$(dirname $0)"
GENIMAGE_CFG="${BOARD_DIR}/genimage.cfg"
GENIMAGE_TMP="${BUILD_DIR}/genimage.tmp"

LINUX_ON_VEXRISCV_OUT_DIR=$BR2_EXTERNAL_LITEX_VEXRISCV_PATH/../images
DST_DTB=$LINUX_ON_VEXRISCV_OUT_DIR/rv32.dtb
DST_OPENSBI=$LINUX_ON_VEXRISCV_OUT_DIR/opensbi.bin
DST_IMAGE=$LINUX_ON_VEXRISCV_OUT_DIR/Image
DST_ROOTFS=$LINUX_ON_VEXRISCV_OUT_DIR/rootfs.cpio

rm -f $DST_OPENSBI $DST_ROOTFS $DST_IMAGE
ln -s $BINARIES_DIR/fw_jump.bin $DST_OPENSBI
ln -s $BINARIES_DIR/Image $DST_IMAGE
ln -s $BINARIES_DIR/rootfs.cpio $DST_ROOTFS

if [ ! -e $DST_DTB ]; then
	echo ""
	echo "Warning: missing file $DST_DTB"
	echo "a dummy file will be created"
	echo "must be replaced manually by required rv32.dtb"
	echo ""
	touch $DST_OPENSBI
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

