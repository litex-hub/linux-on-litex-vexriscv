################################################################################
#
# dhrystone-opt
#
################################################################################

DHRYSTONE_OPT_VERSION = 2
DHRYSTONE_OPT_SOURCE = dhry-c
DHRYSTONE_OPT_SITE = http://www.netlib.org/benchmark

define DHRYSTONE_OPT_EXTRACT_CMDS
	(cd $(@D) && $(SHELL) $(DHRYSTONE_OPT_DL_DIR)/$($(PKG)_SOURCE))
	$(Q)cp $(BR2_EXTERNAL_LITEX_VEXRISCV_PATH)/package/dhrystone-opt/Makefile $(@D)/
	$(Q)cp $(BR2_EXTERNAL_LITEX_VEXRISCV_PATH)/package/dhrystone-opt/*.S $(@D)/
endef

define DHRYSTONE_OPT_BUILD_CMDS
	$(TARGET_CONFIGURE_OPTS) $(MAKE) -C $(@D)
endef

define DHRYSTONE_OPT_INSTALL_TARGET_CMDS
	$(INSTALL) -D $(@D)/dhrystone $(TARGET_DIR)/usr/bin/dhrystone-opt
endef

$(eval $(generic-package))
