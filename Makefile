# Kernel source tree to use
KSRC := ../kernel

# Full .config files provided, and the defconfig files generated from them
CONFIG_SRC := 4.4/x86/siemens_iot2000.config
DEFCONFIG_GEN := $(CONFIG_SRC:%.config=%_defconfig)

# defconfig files provided, and the full .config files generated from them
DEFCONFIG_SRC := $(filter-out $(DEFCONFIG_GEN),$(wildcard */*/*_defconfig))
CONFIG_GEN := $(DEFCONFIG_SRC:%_defconfig=%.config)

ALL_GEN := $(DEFCONFIG_GEN) $(CONFIG_GEN)

all : $(ALL_GEN)
clean :
	rm -f $(ALL_GEN)
.PHONY : all clean

# Convert full .config to defconfig
%_defconfig : VERSION = $(word 1,$(subst /, ,$@))
%_defconfig : ARCH = $(word 2,$(subst /, ,$@))
$(DEFCONFIG_GEN) : %_defconfig : %.config
	cd $(KSRC) && git checkout linux-$(VERSION).y-cip
	cp $< $(KSRC)/.config
	cd $(KSRC) && $(MAKE) ARCH=$(ARCH) savedefconfig
	mv $(KSRC)/defconfig $@

# Convert defconfig to full .config
%.config : VERSION = $(word 1,$(subst /, ,$@))
%.config : ARCH = $(word 2,$(subst /, ,$@))
$(CONFIG_GEN) : %.config : %_defconfig
	cd $(KSRC) && git checkout linux-$(VERSION).y-cip
	cp $< $(KSRC)/arch/$(ARCH)/configs/temp_defconfig
	cd $(KSRC) && $(MAKE) ARCH=$(ARCH) temp_defconfig
	cd $(KSRC) && rm -f $(KSRC)/arch/$(ARCH)/configs/temp_defconfig
	mv $(KSRC)/.config $@
